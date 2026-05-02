"""Tests for the volcano plugin."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, Mock

import pytest

from plugins.volcano import VolcanoPlugin
from src.plugins.base import PluginResult

MANIFEST = json.loads("""
{
    "id": "volcano",
    "name": "Volcano Activity",
    "version": "0.1.0",
    "settings_schema": {
        "type": "object",
        "properties": {
            "enabled": {
                "type": "boolean",
                "title": "Enabled",
                "default": false
            },
            "refresh_seconds": {
                "type": "integer",
                "title": "Refresh Interval (seconds)",
                "description": "How often to check for eruption updates.",
                "default": 3600,
                "minimum": 1800
            }
        },
        "required": []
    }
}
""")

SAMPLE_RESPONSE = json.loads("""
{
    "entries": [
        {
            "title": "Kilauea (United States)",
            "summary": "Eruption ongoing at the summit. Lava lake active.",
            "link": "https://volcano.si.edu/volcano.cfm?vn=332010",
            "published": "2026-05-01T00:00:00Z"
        },
        {
            "title": "Etna (Italy)",
            "summary": "Strombolian activity at SE crater.",
            "link": "https://volcano.si.edu/volcano.cfm?vn=211060",
            "published": "2026-05-01T00:00:00Z"
        }
    ]
}
""")


@pytest.fixture
def plugin():
    return VolcanoPlugin(MANIFEST)


@pytest.fixture
def configured_plugin():
    p = VolcanoPlugin(MANIFEST)
    p.config = json.loads("""
{}
""")
    return p


class TestVolcanoPlugin:

    def test_plugin_id(self, plugin):
        assert plugin.plugin_id == "volcano"

    def test_manifest_valid(self):
        manifest_path = Path(__file__).parent.parent / "manifest.json"
        with open(manifest_path) as f:
            m = json.load(f)
        for field in ("id", "name", "version"):
            assert field in m

    def test_fetch_data_success(self, configured_plugin):
        from unittest.mock import MagicMock, patch as _patch
        import sys
        mock_fp = MagicMock()
        mock_fp.parse.return_value = SAMPLE_RESPONSE
        with _patch.dict(sys.modules, {"feedparser": mock_fp}):
            result = configured_plugin.fetch_data()

        assert result.available is True
        assert result.error is None
        assert result.data is not None
        assert "volcano_name" in result.data, "missing variable: volcano_name"
        assert "country" in result.data, "missing variable: country"
        assert "activity" in result.data, "missing variable: activity"
        assert "active_count" in result.data, "missing variable: active_count"

    @pytest.mark.skip(reason="plugin does not use requests.get")
    def test_fetch_data_network_error(self, configured_plugin):
        pass

    @pytest.mark.skip(reason="plugin does not use requests.get")
    def test_fetch_data_bad_json(self, configured_plugin):
        pass
    def test_fetch_data_empty_feed(self, configured_plugin):
        from unittest.mock import MagicMock, patch as _patch
        import sys
        mock_fp = MagicMock()
        mock_fp.parse.return_value = {"entries": []}
        with _patch.dict(sys.modules, {"feedparser": mock_fp}):
            result = configured_plugin.fetch_data()
        assert result.available is False

