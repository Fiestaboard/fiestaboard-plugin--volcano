"""Display current volcanic eruption alerts from the Smithsonian Global Volcanism Program RSS feed."""

from __future__ import annotations

import logging
from typing import Any, Dict, List
import requests
from src.plugins.base import PluginBase, PluginResult

logger = logging.getLogger(__name__)

API_URL = "https://volcano.si.edu/news/WeeklyVolcanoRSS.xml"
USER_AGENT = "FiestaBoard Volcano Activity Plugin (https://github.com/Fiestaboard/fiestaboard-plugin--volcano)"


class VolcanoPlugin(PluginBase):
    """Volcano Activity plugin for FiestaBoard."""

    @property
    def plugin_id(self) -> str:
        return "volcano"

    def fetch_data(self) -> PluginResult:
        try:
            import feedparser
            feed = feedparser.parse(API_URL)
            entries = feed.get("entries", [])

            if not entries:
                return PluginResult(available=False, error="No RSS entries found")

            latest = entries[0]
            title = latest.get("title", "")
            summary = latest.get("summary", "")

            # Title format is typically "Volcano Name (Country)"
            volcano_name = title.split("(")[0].strip() if "(" in title else title
            country = title.split("(")[1].rstrip(")").strip() if "(" in title else "Unknown"

            # Summarize activity from first sentence of summary
            activity = summary.split(".")[0] if summary else "Activity reported"

            return PluginResult(
                available=True,
                data={
                    "volcano_name": volcano_name,
                    "country": country,
                    "activity": activity,
                    "active_count": len(entries),
                },
            )
        except Exception as e:
            logger.exception("Error fetching volcano data")
            return PluginResult(available=False, error=str(e))

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        return []

    def cleanup(self) -> None:
        pass
