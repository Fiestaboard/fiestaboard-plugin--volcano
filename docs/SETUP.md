# Volcano Activity Setup Guide

Display current volcanic eruption alerts from the Smithsonian Global Volcanism Program weekly report.

## Overview

The Volcano Activity plugin reads the Smithsonian GVP Weekly Volcanic Activity Report RSS feed and shows the volcano at the top of it — the GVP lists new activity and unrest ahead of ongoing activity — plus how many volcanoes are listed as active that week.

- API reference: https://volcano.si.edu/

### Prerequisites

None. No API key, no account, and no extra packages to install — the plugin uses only `requests` and `defusedxml`, which FiestaBoard already ships. It does need outbound access to `volcano.si.edu`.

## Quick Setup

1. **Enable** — Go to **Integrations** in your FiestaBoard settings and enable **Volcano Activity**.
2. **Configure** — Optionally adjust the refresh interval (see Configuration Reference below). The defaults are fine.
3. **Template** — Add a page using the `volcano` plugin variables:
   ```
   VOLCANO ACTIVITY
   {{volcano.volcano_name}}
   {{volcano.country}}
   {{volcano.activity}}
   ```
4. **View** — Navigate to your board page to see the live display.

## Template Variables

| Variable | Description | Example |
|---|---|---|
| `volcano.volcano_name` | Volcano at the top of this week's report | `Asosan` |
| `volcano.country` | Country that volcano is in | `Japan` |
| `volcano.activity` | Activity status from the report | `New Unrest` |
| `volcano.active_count` | Number of volcanoes listed as active this week | `21` |

`volcano.activity` is one of `New Unrest`, `Ongoing Unrest`, `New Eruption`, or `Ongoing Eruption` — the GVP's own statuses, shortened to fit a board line. See the [README](../README.md#activity-values) for the mapping.

## Configuration Reference

| Setting | Name | Description | Default |
|---|---|---|---|
| `enabled` | Enabled |  | `False` |
| `refresh_seconds` | Refresh Interval (seconds) | How often to check for eruption updates. | `3600` |

The report is published once a week, so the 3600s default already refreshes far more often than the data changes.

## Troubleshooting

- **No data** — verify the FiestaBoard host can reach `volcano.si.edu`. The plugin gives up after 15 seconds and reports the connection error on the Integrations page.
- **`Malformed RSS from volcano.si.edu`** — the feed returned something that is not valid XML, usually an error page from an outage upstream. It will recover on its own; check https://volcano.si.edu/ if it persists.
- **A volcano name looks truncated** — board lines are 22 tiles on a Flagship and 15 on a Note. Use a shorter line or drop `{{volcano.country}}` to make room.
