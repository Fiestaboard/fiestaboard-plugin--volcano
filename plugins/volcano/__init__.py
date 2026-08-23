"""Display current volcanic eruption alerts from the Smithsonian Global Volcanism Program RSS feed."""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List

import requests
from defusedxml import DefusedXmlException
from defusedxml import ElementTree as ET

from src.plugins.base import PluginBase, PluginResult

logger = logging.getLogger(__name__)

API_URL = "https://volcano.si.edu/news/WeeklyVolcanoRSS.xml"
USER_AGENT = "FiestaBoard Volcano Activity Plugin (https://github.com/Fiestaboard/fiestaboard-plugin--volcano)"
REQUEST_TIMEOUT = 15

# GVP weekly-report item titles are strictly formatted:
#
#   Asosan (Japan) - Report for 13 August-19 August 2026 - New Unrest
#   Rincon de la Vieja (Costa Rica) - Report for 13 August-19 August 2026 - Continuing Eruptive Activity
#
# i.e. "<volcano> (<country>) - Report for <dates> - <status>". The status is
# the last dash-separated segment; the report dates in the middle are of no
# use on a board.
_TITLE = re.compile(r"^\s*(?P<name>.+?)\s*\((?P<country>[^)]*)\)\s*(?:-\s*(?P<rest>.*?))?\s*$")

# The GVP's status vocabulary is fixed and too wide for a 22-tile Flagship
# line ("Continuing Eruptive Activity" is 28 characters). These are the same
# statements in board-sized wording; anything unrecognised is passed through
# verbatim rather than mangled.
_STATUS_SHORT = {
    "new eruptive activity": "New Eruption",
    "continuing eruptive activity": "Ongoing Eruption",
    "new unrest": "New Unrest",
    "continuing unrest": "Ongoing Unrest",
}


def parse_title(title: str) -> tuple[str, str, str]:
    """Split a GVP report title into (volcano name, country, activity status).

    Falls back to the whole title as the name when it does not match the
    documented shape, so an upstream format change degrades to something
    readable instead of to nonsense.
    """
    match = _TITLE.match(title or "")
    if not match:
        return (title or "").strip(), "", ""

    name = match.group("name").strip()
    country = match.group("country").strip()

    rest = (match.group("rest") or "").strip()
    status = rest.rsplit(" - ", 1)[-1].strip() if rest else ""
    activity = _STATUS_SHORT.get(status.lower(), status)

    return name, country, activity


class VolcanoPlugin(PluginBase):
    """Volcano Activity plugin for FiestaBoard."""

    @property
    def plugin_id(self) -> str:
        return "volcano"

    def fetch_data(self) -> PluginResult:
        try:
            response = requests.get(
                API_URL,
                timeout=REQUEST_TIMEOUT,
                headers={"User-Agent": USER_AGENT},
            )
            response.raise_for_status()
            root = ET.fromstring(response.content)
        except requests.RequestException as e:
            logger.warning("Volcano feed request failed: %s", e)
            return PluginResult(available=False, error=f"Could not reach volcano.si.edu: {e}")
        except (ET.ParseError, DefusedXmlException) as e:
            logger.warning("Volcano feed is not usable XML: %s", e)
            return PluginResult(available=False, error=f"Malformed RSS from volcano.si.edu: {e}")

        items = root.findall("./channel/item")
        if not items:
            return PluginResult(available=False, error="No RSS entries found")

        # The weekly report lists new activity before ongoing activity, so the
        # first item is the week's most notable volcano.
        volcano_name, country, activity = parse_title(items[0].findtext("title") or "")

        return PluginResult(
            available=True,
            data={
                "volcano_name": volcano_name,
                "country": country,
                "activity": activity,
                "active_count": len(items),
            },
        )

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        return []

    def cleanup(self) -> None:
        pass
