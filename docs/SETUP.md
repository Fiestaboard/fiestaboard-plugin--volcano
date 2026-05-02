# Volcano Activity Setup Guide

Display current volcanic eruption alerts from the Smithsonian Global Volcanism Program RSS feed.

## Overview

The Volcano Activity plugin parses the Smithsonian GVP weekly activity report RSS feed to show the most recently active volcanoes worldwide. No API key required. Uses feedparser to parse RSS.

- API reference: https://volcano.si.edu/

### Prerequisites

No API key or account required. Requires `feedparser` (installed automatically).

## Quick Setup

1. **Enable** — Go to **Integrations** in your FiestaBoard settings and enable **Volcano Activity**.
2. **Configure** — Fill in the plugin settings (see Configuration Reference below).
3. **Template** — Add a page using the `volcano` plugin variables:
   ```
   {{{ volcano.status }}}
   ```
4. **View** — Navigate to your board page to see the live display.

## Template Variables

| Variable | Description | Example |
|---|---|---|
| `volcano.volcano_name` | Name of the most recently active volcano | `Kilauea` |
| `volcano.country` | Country of the most recently active volcano | `United States` |
| `volcano.activity` | Brief activity description | `Eruption ongoing` |
| `volcano.active_count` | Number of volcanoes listed as active this week | `12` |

## Configuration Reference

| Setting | Name | Description | Default |
|---|---|---|---|
| `enabled` | Enabled |  | `False` |
| `refresh_seconds` | Refresh Interval (seconds) | How often to check for eruption updates. | `3600` |

## Troubleshooting

- **No data** — verify connectivity to `volcano.si.edu`.
- **feedparser not installed** — rebuild the Docker container after adding to `requirements.txt`.

