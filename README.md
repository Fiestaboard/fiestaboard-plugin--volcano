# Volcano Activity Plugin

Display current volcanic eruption alerts from the Smithsonian Global Volcanism Program RSS feed.

![Volcano Activity Display](./docs/board-display.png)

**→ [Setup Guide](./docs/SETUP.md)**

## Overview

The Volcano Activity plugin parses the Smithsonian GVP weekly activity report RSS feed to show the most recently active volcanoes worldwide. No API key required. Uses feedparser to parse RSS.

## Template Variables

| Variable | Description | Example |
|---|---|---|
| `volcano.volcano_name` | Name of the most recently active volcano | `Kilauea` |
| `volcano.country` | Country of the most recently active volcano | `United States` |
| `volcano.activity` | Brief activity description | `Eruption ongoing` |
| `volcano.active_count` | Number of volcanoes listed as active this week | `12` |

## Example Templates

```
VOLCANO ACTIVITY
{{volcano.volcano_name}}
{{volcano.country}}
{{volcano.activity}}
Active this week: {{volcano.active_count}}

```

## Configuration

| Setting | Name | Description | Required |
|---|---|---|---|
| `refresh_seconds` | Refresh Interval | How often to fetch data (seconds) | No |

## Features

- Smithsonian GVP weekly RSS feed
- Most recently active volcano name and country
- Activity description
- Active volcano count
- No API key required

## Author

FiestaBoard Team
