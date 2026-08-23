"""Tests for the volcano plugin."""

from __future__ import annotations

import json
import re
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

from plugins.volcano import VolcanoPlugin, parse_title

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE = Path(__file__).parent / "fixtures" / "weekly_report.xml"

MANIFEST = json.loads((REPO_ROOT / "manifest.json").read_text())


def _feed_bytes() -> bytes:
    """A real GVP weekly report, captured from volcano.si.edu."""
    return FIXTURE.read_bytes()


def _mock_get(content: bytes = None, status: int = 200, exc: Exception = None):
    """Patch requests.get in the plugin module."""
    response = MagicMock()
    response.content = content if content is not None else _feed_bytes()
    response.status_code = status
    if status >= 400:
        response.raise_for_status.side_effect = requests.HTTPError(f"{status}")
    else:
        response.raise_for_status.return_value = None
    return patch(
        "plugins.volcano.requests.get",
        side_effect=exc if exc else None,
        return_value=None if exc else response,
    )


@pytest.fixture
def plugin():
    return VolcanoPlugin(MANIFEST)


@pytest.fixture
def configured_plugin():
    p = VolcanoPlugin(MANIFEST)
    p.config = {}
    return p


class TestParseTitle:
    """The GVP title format, which is the whole job of this plugin."""

    def test_country_is_the_parenthesised_country_only(self):
        """Regression: the country field used to swallow the rest of the title.

        ``title.split("(")[1].rstrip(")")`` returned everything after the open
        paren, and the trailing ``rstrip(")")`` was a no-op because a GVP title
        does not end in ``)``. Users saw 70 characters of report metadata in a
        field the manifest sizes for a country name.
        """
        _, country, _ = parse_title("Asosan (Japan) - Report for 13 August-19 August 2026 - New Unrest")
        assert country == "Japan"

    def test_name_is_the_volcano(self):
        name, _, _ = parse_title("Rincon de la Vieja (Costa Rica) - Report for 13 August-19 August 2026 - Continuing Eruptive Activity")
        assert name == "Rincon de la Vieja"

    def test_activity_is_the_status_not_the_report_dates(self):
        """The status is the last dash-separated segment, not the date range."""
        _, _, activity = parse_title("Etna (Italy) - Report for 13 August-19 August 2026 - New Eruptive Activity")
        assert activity == "New Eruption"

    @pytest.mark.parametrize(
        "status,expected",
        [
            ("New Unrest", "New Unrest"),
            ("Continuing Unrest", "Ongoing Unrest"),
            ("New Eruptive Activity", "New Eruption"),
            ("Continuing Eruptive Activity", "Ongoing Eruption"),
        ],
    )
    def test_known_statuses_are_shortened_to_fit_a_board_line(self, status, expected):
        _, _, activity = parse_title(f"Aira (Japan) - Report for 1 January-7 January 2026 - {status}")
        assert activity == expected

    def test_unknown_status_passes_through_verbatim(self):
        """An upstream vocabulary change must degrade to readable, not to blank."""
        _, _, activity = parse_title("Aira (Japan) - Report for 1 January-7 January 2026 - Sudden Cataclysm")
        assert activity == "Sudden Cataclysm"

    def test_title_without_the_documented_shape_becomes_the_name(self):
        name, country, activity = parse_title("Something Unexpected")
        assert name == "Something Unexpected"
        assert country == ""
        assert activity == ""

    def test_title_with_country_but_no_status(self):
        name, country, activity = parse_title("Kilauea (United States)")
        assert (name, country, activity) == ("Kilauea", "United States", "")


class TestVolcanoPlugin:
    def test_plugin_id(self, plugin):
        assert plugin.plugin_id == "volcano"

    def test_manifest_valid(self):
        for field in ("id", "name", "version"):
            assert field in MANIFEST

    def test_fetch_data_returns_the_first_report_in_the_feed(self, configured_plugin):
        with _mock_get():
            result = configured_plugin.fetch_data()

        assert result.available is True
        assert result.error is None
        assert result.data == {
            "volcano_name": "Asosan",
            "country": "Japan",
            "activity": "New Unrest",
            "active_count": 21,
        }

    def test_every_real_title_yields_a_clean_country(self, configured_plugin):
        """Guard the whole feed, not just its first entry.

        The original bug produced a country containing ``)``, the report date
        range, and the status. Nothing in the feed should parse that way.
        """
        from defusedxml import ElementTree as ET

        root = ET.fromstring(_feed_bytes())
        titles = [(item.findtext("title") or "") for item in root.findall("./channel/item")]
        assert len(titles) > 5, "fixture is too thin to prove anything"

        max_country = MANIFEST["variables"]["simple"]["country"]["max_length"]
        for title in titles:
            name, country, activity = parse_title(title)
            assert ")" not in country, f"{title!r} -> country {country!r}"
            assert "Report for" not in country, f"{title!r} -> country {country!r}"
            assert len(country) <= max_country, f"{title!r} -> country {country!r} exceeds max_length"
            assert country, f"{title!r} produced no country"
            assert name and "(" not in name, f"{title!r} -> name {name!r}"
            assert activity, f"{title!r} produced no activity"

    def test_parsed_values_fit_their_declared_max_lengths(self, configured_plugin):
        with _mock_get():
            result = configured_plugin.fetch_data()

        simple = MANIFEST["variables"]["simple"]
        for name, value in result.data.items():
            assert len(str(value)) <= simple[name]["max_length"], f"{name}={value!r} overflows its declared max_length"

    def test_fetch_data_network_error(self, configured_plugin):
        with _mock_get(exc=requests.ConnectionError("no route to host")):
            result = configured_plugin.fetch_data()
        assert result.available is False
        assert "volcano.si.edu" in result.error

    def test_fetch_data_http_error(self, configured_plugin):
        with _mock_get(status=503):
            result = configured_plugin.fetch_data()
        assert result.available is False

    def test_fetch_data_malformed_xml(self, configured_plugin):
        with _mock_get(content=b"<rss><channel><item></channel>"):
            result = configured_plugin.fetch_data()
        assert result.available is False
        assert "Malformed" in result.error

    def test_fetch_data_rejects_hostile_xml(self, configured_plugin):
        """defusedxml refuses entity expansion; the plugin must not leak that."""
        hostile = b'<!DOCTYPE r [<!ENTITY x "boom">]><rss><channel><item><title>&x;</title></item></channel></rss>'
        with _mock_get(content=hostile):
            result = configured_plugin.fetch_data()
        assert result.available is False

    def test_fetch_data_empty_feed(self, configured_plugin):
        with _mock_get(content=b"<rss><channel></channel></rss>"):
            result = configured_plugin.fetch_data()
        assert result.available is False
        assert result.error == "No RSS entries found"

    def test_fetch_data_sends_a_timeout(self, configured_plugin):
        """feedparser.parse(url) did its own fetch with no timeout at all."""
        with _mock_get() as mock:
            configured_plugin.fetch_data()
        assert mock.call_args.kwargs.get("timeout"), "request was made without a timeout"


class TestRuntimeDependencies:
    """FiestaBoard never installs a plugin's requirements.txt.

    A plugin that declares one is broken on every real install -- that is what
    Fiestaboard/FiestaBoard#1690 caught here. This test fails if a
    non-importable dependency is ever reintroduced.
    """

    def test_no_undeclarable_third_party_dependency(self):
        req = REPO_ROOT / "requirements.txt"
        if not req.exists():
            return

        import importlib.util

        overrides = {"pyyaml": "yaml", "python-dateutil": "dateutil", "beautifulsoup4": "bs4"}
        for line in req.read_text().splitlines():
            line = line.split("#")[0].strip()
            if not line or line.startswith("-"):
                continue
            dist = re.match(r"^[A-Za-z0-9._-]+", line).group(0)
            module = overrides.get(dist.lower(), dist.replace("-", "_"))
            assert importlib.util.find_spec(module) is not None, (
                f"requirements.txt declares {dist!r}, which FiestaBoard does not ship "
                f"and does not install. The plugin cannot work on a real install."
            )

    def test_source_does_not_import_feedparser(self):
        source = (REPO_ROOT / "plugins" / "volcano" / "__init__.py").read_text()
        assert "feedparser" not in source
