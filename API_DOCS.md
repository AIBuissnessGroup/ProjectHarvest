# FN Create API Documentation

**Base URL:** `https://api.fncreate.gg`

---

## Table of Contents

- [Authentication](#authentication)
- [Rate Limiting](#rate-limiting)
- [Maps](#maps)
  - [Search Maps](#search-maps)
  - [Get Maps by CCU](#get-maps-by-ccu)
  - [Get Map Details](#get-map-details)
  - [Get Map CCU History](#get-map-ccu-history)
  - [Get Map Discovery History](#get-map-discovery-history)
  - [Get Map Changelog](#get-map-changelog)
  - [Check Map in Discovery](#check-map-in-discovery)
  - [Get Total CCU History](#get-total-ccu-history)
- [Discovery](#discovery)
  - [Get Full Discovery](#get-full-discovery)
  - [Get Discovery Stats](#get-discovery-stats)
  - [Get Discovery Panels](#get-discovery-panels)
  - [Get Discovery Surface](#get-discovery-surface)
  - [Get Game Collections](#get-game-collections)
  - [Get Collection by ID](#get-collection-by-id)
- [Creators](#creators)
  - [Search Creators](#search-creators)
  - [Get Creators by CCU](#get-creators-by-ccu)
  - [Get Creators by Followers](#get-creators-by-followers)
  - [Get Creators by Map Count](#get-creators-by-map-count)
  - [Get Creators in Discovery](#get-creators-in-discovery)
  - [Get Creator Profile](#get-creator-profile)
  - [Get Creator CCU History](#get-creator-ccu-history)
  - [Get Creator Changelog](#get-creator-changelog)
  - [Get Creator Maps](#get-creator-maps)
- [Statistics](#statistics)
  - [Get Creative Stats](#get-creative-stats)
  - [Get 24-Hour Stats](#get-24-hour-stats)
  - [Get Release Stats](#get-release-stats)
  - [Get Genre Stats](#get-genre-stats)
  - [Get Weekday Stats](#get-weekday-stats)
  - [Get Mode Distribution Stats](#get-mode-distribution-stats)
- [Error Handling](#error-handling)

---

## Authentication

Most data endpoints are **public** and do not require authentication.

---

## Rate Limiting

- **Rate Limit:** 100 requests per 15 minutes per IP
- **Headers:** Rate limit information is returned in response headers
- **Error Response:** `429 Too Many Requests` when limit exceeded

---

## Maps

### Search Maps

Search for maps with various filters.

```
GET /api/maps/search
```

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `q` | string | - | Search query (searches title, tagline, code, tags) |
| `genre` | string | - | Filter by genre (e.g., "Gun Game", "Parkour") |
| `category` | string | - | Filter by category (e.g., "Combat", "Adventure") |
| `tags` | string | - | Filter by description tags |
| `minPlayers` | number | - | Minimum current player count |
| `maxPlayers` | number | - | Maximum current player count |
| `inDiscovery` | boolean | - | Filter maps currently in discovery |
| `noepic` | boolean | - | Exclude Epic-made maps |
| `sort` | string | - | Sort by: `popular` (CCU), `trending` (7d avg), `new` (publish date) |
| `page` | number | 1 | Page number |
| `limit` | number | 20 | Results per page (max: 100) |

#### Example Request

```bash
curl "https://api.fncreate.gg/api/maps/search?q=parkour&genre=Parkour&sort=popular&limit=10"
```

#### Example Response

```json
{
  "total": 1523,
  "page": 1,
  "limit": 10,
  "maps": [
    {
      "mnemonic": "1234-5678-9012",
      "title": "Ultimate Parkour Challenge",
      "tagline": "100 levels of parkour madness",
      "currentCCU": 15420,
      "peakCCU24h": 28000,
      "avgCCU7d": 12500,
      "inDiscovery": true,
      "creatorName": "CreatorExample",
      "creatorAccountId": "abc123",
      "published": "2025-01-15T10:30:00Z",
      "metadata": {
        "title": "Ultimate Parkour Challenge",
        "tagline": "100 levels of parkour madness",
        "generated_image_urls": {
          "url_s": "https://cdn.example.com/map-thumb-small.jpg",
          "url_m": "https://cdn.example.com/map-thumb-medium.jpg"
        }
      }
    }
  ]
}
```

---

### Get Maps by CCU

Get maps ranked by current concurrent users.

```
GET /api/maps/by-ccu
```

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `genre` | string | - | Filter by genre |
| `category` | string | - | Filter by category |
| `tags` | string | - | Filter by tags |
| `minPlayers` | number | - | Minimum CCU |
| `maxPlayers` | number | - | Maximum CCU |
| `inDiscovery` | boolean | - | Only maps in discovery |
| `noepic` | boolean | - | Exclude Epic maps |
| `page` | number | 1 | Page number |
| `limit` | number | 20 | Results per page (max: 100) |

#### Example Request

```bash
curl "https://api.fncreate.gg/api/maps/by-ccu?inDiscovery=true&limit=20"
```

---

### Get Map Details

Get detailed information about a specific map.

```
GET /api/maps/:code
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `code` | string | Island code (e.g., "1234-5678-9012") |

#### Example Request

```bash
curl "https://api.fncreate.gg/api/maps/1234-5678-9012"
```

#### Example Response

```json
{
  "mnemonic": "1234-5678-9012",
  "linkCode": "1234-5678-9012",
  "title": "Ultimate Parkour Challenge",
  "tagline": "100 levels of parkour madness",
  "currentCCU": 15420,
  "peakCCU24h": 28000,
  "avgCCU7d": 12500,
  "avgCCU30d": 11200,
  "allTimePeakCCU": 45000,
  "inDiscovery": true,
  "discoveryPanels": ["Featured", "Popular This Week"],
  "creatorName": "CreatorExample",
  "creatorAccountId": "abc123",
  "published": "2025-01-15T10:30:00Z",
  "lastUpdated": "2025-01-18T14:20:00Z",
  "metadata": {
    "title": "Ultimate Parkour Challenge",
    "tagline": "100 levels of parkour madness",
    "introduction": "Welcome to the ultimate parkour experience...",
    "generated_image_urls": {
      "url_s": "https://cdn.example.com/map-thumb-small.jpg",
      "url_m": "https://cdn.example.com/map-thumb-medium.jpg"
    },
    "image_urls": {
      "url_s": "https://cdn.example.com/map-image-small.jpg",
      "url_m": "https://cdn.example.com/map-image-medium.jpg"
    }
  }
}
```

---

### Get Map CCU History

Get historical CCU data for a specific map.

```
GET /api/maps/:code/ccu-history
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `code` | string | Island code |

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `period` | string | `7d` | Time period: `1d`, `7d`, `1m`, `1y`, `all` |

#### Example Request

```bash
curl "https://api.fncreate.gg/api/maps/1234-5678-9012/ccu-history?period=7d"
```

#### Example Response

```json
{
  "code": "1234-5678-9012",
  "period": "7d",
  "dataPoints": [
    {
      "timestamp": "2025-01-13T00:00:00Z",
      "ccu": 12500,
      "peakCCU": 18000
    },
    {
      "timestamp": "2025-01-14T00:00:00Z",
      "ccu": 13200,
      "peakCCU": 19500
    }
  ],
  "summary": {
    "avgCCU": 13450,
    "peakCCU": 28000,
    "minCCU": 8500,
    "totalDataPoints": 168
  }
}
```

---

### Get Map Discovery History

Get discovery placement history for a map.

```
GET /api/maps/:code/discovery-history
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `code` | string | Island code |

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `period` | string | `7d` | Time period: `1d`, `7d`, `1m`, `3m`, `6m`, `1y`, `all` |

#### Example Request

```bash
curl "https://api.fncreate.gg/api/maps/1234-5678-9012/discovery-history?period=1m"
```

#### Example Response

```json
{
  "code": "1234-5678-9012",
  "period": "1m",
  "events": [
    {
      "timestamp": "2025-01-10T14:30:00Z",
      "event": "entered_discovery",
      "panel": "Featured"
    },
    {
      "timestamp": "2025-01-12T08:15:00Z",
      "event": "panel_change",
      "fromPanel": "Featured",
      "toPanel": "Popular This Week"
    },
    {
      "timestamp": "2025-01-15T22:00:00Z",
      "event": "left_discovery",
      "panel": "Popular This Week"
    }
  ],
  "summary": {
    "totalTimeInDiscovery": "5d 7h 30m",
    "panelsAppeared": ["Featured", "Popular This Week"],
    "currentlyInDiscovery": false
  }
}
```

---

### Get Map Changelog

Get metadata change history for a map.

```
GET /api/maps/:code/changelog
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `code` | string | Island code |

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | number | 50 | Max entries (max: 100) |

#### Example Request

```bash
curl "https://api.fncreate.gg/api/maps/1234-5678-9012/changelog?limit=20"
```

#### Example Response

```json
{
  "code": "1234-5678-9012",
  "changes": [
    {
      "timestamp": "2025-01-18T14:20:00Z",
      "field": "tagline",
      "oldValue": "50 levels of parkour",
      "newValue": "100 levels of parkour madness"
    },
    {
      "timestamp": "2025-01-15T10:30:00Z",
      "field": "title",
      "oldValue": "Parkour Challenge",
      "newValue": "Ultimate Parkour Challenge"
    }
  ],
  "total": 2
}
```

---

### Check Map in Discovery

Check if a map is currently in Fortnite's discovery browser.

```
GET /api/maps/:code/discovery-check
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `code` | string | Island code |

#### Example Request

```bash
curl "https://api.fncreate.gg/api/maps/1234-5678-9012/discovery-check"
```

#### Example Response

```json
{
  "code": "1234-5678-9012",
  "inDiscovery": true,
  "panels": [
    {
      "id": "featured",
      "displayName": "Featured",
      "position": 3
    },
    {
      "id": "popular_this_week",
      "displayName": "Popular This Week",
      "position": 12
    }
  ],
  "lastChecked": "2025-01-20T10:00:00Z"
}
```

---

### Get Total CCU History

Get historical total CCU across all Fortnite Creative maps.

```
GET /api/maps/total-ccu-history
```

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `period` | string | `7d` | Time period: `1d`, `7d`, `1m`, `1y`, `all` |

#### Example Request

```bash
curl "https://api.fncreate.gg/api/maps/total-ccu-history?period=7d"
```

#### Example Response

```json
{
  "period": "7d",
  "dataPoints": [
    {
      "timestamp": "2025-01-13T00:00:00Z",
      "totalCCU": 2500000,
      "mapCount": 45000
    },
    {
      "timestamp": "2025-01-14T00:00:00Z",
      "totalCCU": 2650000,
      "mapCount": 45120
    }
  ],
  "summary": {
    "avgTotalCCU": 2575000,
    "peakTotalCCU": 3200000,
    "avgMapsWithPlayers": 12500
  }
}
```

---

## Discovery

### Get Full Discovery

Get all maps currently in Fortnite's discovery browser.

```
GET /api/discovery
```

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `region` | string | `all` | Filter by region or `all` |
| `page` | number | 1 | Page number |
| `limit` | number | 50 | Results per page (max: 200) |

#### Example Request

```bash
curl "https://api.fncreate.gg/api/discovery?page=1&limit=50"
```

#### Example Response

```json
{
  "region": "all",
  "total": 2500,
  "page": 1,
  "limit": 50,
  "totalPages": 50,
  "maps": [
    {
      "mnemonic": "1234-5678-9012",
      "title": "Ultimate Parkour Challenge",
      "currentCCU": 15420,
      "panel": "Featured",
      "position": 3,
      "creatorName": "CreatorExample"
    }
  ]
}
```

---

### Get Discovery Stats

Get discovery overview with statistics and total CCU.

```
GET /api/discovery/stats
```

#### Example Request

```bash
curl "https://api.fncreate.gg/api/discovery/stats"
```

#### Example Response

```json
{
  "surface": "overview",
  "region": "all",
  "totalMapsInDiscovery": 2500,
  "totalCCU": 2800000,
  "avgCCUPerMap": 1120,
  "topGenres": [
    { "genre": "Parkour", "mapCount": 450, "totalCCU": 520000 },
    { "genre": "Gun Game", "mapCount": 380, "totalCCU": 480000 }
  ],
  "lastUpdated": "2025-01-20T10:00:00Z"
}
```

---

### Get Discovery Panels

Get all available discovery panels with display names.

```
GET /api/discovery/panels
```

#### Example Request

```bash
curl "https://api.fncreate.gg/api/discovery/panels"
```

#### Example Response

```json
{
  "total": 45,
  "panels": [
    { "id": "featured", "displayName": "Featured", "category": "curated" },
    { "id": "popular_this_week", "displayName": "Popular This Week", "category": "trending" },
    { "id": "parkour", "displayName": "Parkour", "category": "genre" }
  ],
  "byCategory": {
    "curated": [
      { "id": "featured", "displayName": "Featured" }
    ],
    "trending": [
      { "id": "popular_this_week", "displayName": "Popular This Week" }
    ],
    "genre": [
      { "id": "parkour", "displayName": "Parkour" }
    ]
  }
}
```

---

### Get Discovery Surface

Get maps from a specific discovery surface/panel.

```
GET /api/discovery/:surface
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `surface` | string | Panel ID (e.g., "featured", "parkour") |

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `region` | string | `all` | Filter by region |
| `page` | number | 1 | Page number |
| `limit` | number | 50 | Results per page (max: 200) |

#### Example Request

```bash
curl "https://api.fncreate.gg/api/discovery/featured?page=1&limit=20"
```

#### Example Response

```json
{
  "surface": "featured",
  "region": "all",
  "total": 50,
  "page": 1,
  "limit": 20,
  "totalPages": 3,
  "maps": [
    {
      "mnemonic": "1234-5678-9012",
      "title": "Ultimate Parkour Challenge",
      "currentCCU": 15420,
      "position": 1,
      "creatorName": "CreatorExample"
    }
  ]
}
```

---

### Get Game Collections

Get all game collections (brand collaborations like LEGO, Rocket Racing, etc.).

```
GET /api/discovery/collections
```

#### Example Request

```bash
curl "https://api.fncreate.gg/api/discovery/collections"
```

#### Example Response

```json
{
  "total": 8,
  "collections": [
    {
      "id": "lego",
      "name": "LEGO Fortnite",
      "description": "LEGO-themed creative experiences",
      "mapCount": 125
    },
    {
      "id": "rocket_racing",
      "name": "Rocket Racing",
      "description": "Racing experiences",
      "mapCount": 45
    }
  ]
}
```

---

### Get Collection by ID

Get details for a specific game collection.

```
GET /api/discovery/collections/:collectionId
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `collectionId` | string | Collection ID |

#### Example Request

```bash
curl "https://api.fncreate.gg/api/discovery/collections/lego"
```

---

## Creators

### Search Creators

Search for map creators.

```
GET /api/creators/search
```

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `q` | string | - | Search query |
| `page` | number | 1 | Page number |
| `limit` | number | 20 | Results per page |

#### Example Request

```bash
curl "https://api.fncreate.gg/api/creators/search?q=example&limit=10"
```

---

### Get Creators by CCU

Get creators ranked by total CCU across all their maps.

```
GET /api/creators/by-ccu
```

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | number | 1 | Page number |
| `limit` | number | 20 | Results per page |

#### Example Request

```bash
curl "https://api.fncreate.gg/api/creators/by-ccu?page=1&limit=20"
```

#### Example Response

```json
{
  "total": 15000,
  "page": 1,
  "limit": 20,
  "creators": [
    {
      "account_id": "abc123",
      "display_name": "TopCreator",
      "total_ccu": 125000,
      "map_count": 15,
      "has_discovery_badge": true,
      "follower_count": 50000
    }
  ]
}
```

---

### Get Creators by Followers

Get creators ranked by follower count.

```
GET /api/creators/by-followers
```

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | number | 1 | Page number |
| `limit` | number | 20 | Results per page |

---

### Get Creators by Map Count

Get creators ranked by number of maps published.

```
GET /api/creators/by-maps
```

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | number | 1 | Page number |
| `limit` | number | 20 | Results per page |

---

### Get Creators in Discovery

Get creators who currently have maps in discovery.

```
GET /api/creators/in-discovery
```

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | number | 1 | Page number |
| `limit` | number | 20 | Results per page |

#### Example Request

```bash
curl "https://api.fncreate.gg/api/creators/in-discovery?limit=20"
```

---

### Get Creator Profile

Get detailed creator profile information.

```
GET /api/creators/:id
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Creator account ID |

#### Example Request

```bash
curl "https://api.fncreate.gg/api/creators/abc123"
```

#### Example Response

```json
{
  "account_id": "abc123",
  "display_name": "TopCreator",
  "bio": "Creating awesome Fortnite maps",
  "total_ccu": 125000,
  "map_count": 15,
  "follower_count": 50000,
  "has_discovery_badge": true,
  "images": {
    "avatar": "https://cdn.example.com/avatar.jpg"
  },
  "social_links": {
    "youtube": "https://youtube.com/@topcreator",
    "twitter": "https://twitter.com/topcreator"
  },
  "discoveryBadge": {
    "earned": true,
    "earnedAt": "2024-06-15T00:00:00Z",
    "totalDiscoveryAppearances": 45
  }
}
```

---

### Get Creator CCU History

Get historical CCU data for a creator (total across all maps).

```
GET /api/creators/:id/ccu-history
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Creator account ID |

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `period` | string | `7d` | Time period: `1d`, `7d`, `1m`, `1y`, `all` |
| `breakdown` | boolean | `false` | Show per-map breakdown |

#### Example Request

```bash
curl "https://api.fncreate.gg/api/creators/abc123/ccu-history?period=7d&breakdown=true"
```

#### Example Response

```json
{
  "creatorId": "abc123",
  "period": "7d",
  "dataPoints": [
    {
      "timestamp": "2025-01-13T00:00:00Z",
      "totalCCU": 120000,
      "breakdown": [
        { "mapCode": "1234-5678-9012", "ccu": 45000 },
        { "mapCode": "2345-6789-0123", "ccu": 35000 }
      ]
    }
  ],
  "summary": {
    "avgTotalCCU": 118000,
    "peakTotalCCU": 145000
  }
}
```

---

### Get Creator Changelog

Get profile change history for a creator.

```
GET /api/creators/:id/changelog
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Creator account ID |

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | number | 50 | Max entries (max: 100) |

---

### Get Creator Maps

Get all maps published by a specific creator.

```
GET /api/creators/:id/maps
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Creator account ID |

#### Example Request

```bash
curl "https://api.fncreate.gg/api/creators/abc123/maps"
```

#### Example Response

```json
{
  "total": 15,
  "maps": [
    {
      "mnemonic": "1234-5678-9012",
      "title": "Ultimate Parkour Challenge",
      "tagline": "100 levels of parkour madness",
      "imageUrl": "https://cdn.example.com/map-thumb.jpg",
      "currentCCU": 45000,
      "peakCCU24h": 52000,
      "avgCCU7d": 42000,
      "published": "2025-01-15T10:30:00Z",
      "inDiscovery": true
    }
  ]
}
```

---

## Statistics

### Get Creative Stats

Get overall Fortnite Creative statistics.

```
GET /api/stats/creative
```

#### Example Request

```bash
curl "https://api.fncreate.gg/api/stats/creative"
```

#### Example Response

```json
{
  "totalMaps": 250000,
  "totalCreators": 85000,
  "totalCCU": 2800000,
  "mapsInDiscovery": 2500,
  "avgCCUPerMap": 11.2,
  "lastUpdated": "2025-01-20T10:00:00Z"
}
```

---

### Get 24-Hour Stats

Get activity statistics for the last 24 hours.

```
GET /api/stats/24h
```

#### Example Request

```bash
curl "https://api.fncreate.gg/api/stats/24h"
```

#### Example Response

```json
{
  "newMaps": 450,
  "updatedMaps": 1200,
  "peakTotalCCU": 3500000,
  "avgTotalCCU": 2800000,
  "newCreators": 85,
  "discoveryChanges": 320,
  "period": {
    "start": "2025-01-19T10:00:00Z",
    "end": "2025-01-20T10:00:00Z"
  }
}
```

---

### Get Release Stats

Get map release statistics over time.

```
GET /api/stats/releases
```

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `period` | string | `all` | Time period: `1w`, `1m`, `1y`, `all` |
| `tag` | string | - | Filter by tag (optional) |
| `details` | boolean | `false` | Return map details instead of counts |
| `hasVideo` | boolean | `false` | Filter maps with video trailers (only when details=true) |
| `page` | number | 1 | Page number (only when details=true) |
| `limit` | number | 20 | Results per page (max: 100, only when details=true) |

#### Example Request

```bash
curl "https://api.fncreate.gg/api/stats/releases?period=1m"
```

#### Example Response

```json
{
  "period": "1m",
  "releases": [
    { "date": "2025-01-01", "count": 320 },
    { "date": "2025-01-02", "count": 285 }
  ],
  "summary": {
    "totalReleases": 9500,
    "avgPerDay": 306,
    "peakDay": { "date": "2025-01-15", "count": 520 }
  }
}
```

---

### Get Genre Stats

Get genre statistics with current player counts.

```
GET /api/stats/genres
```

#### Example Request

```bash
curl "https://api.fncreate.gg/api/stats/genres"
```

#### Example Response

```json
{
  "genres": [
    {
      "genre": "Parkour",
      "mapCount": 25000,
      "totalCCU": 650000,
      "avgCCUPerMap": 26,
      "percentOfTotalCCU": 23.2
    },
    {
      "genre": "Gun Game",
      "mapCount": 22000,
      "totalCCU": 580000,
      "avgCCUPerMap": 26.4,
      "percentOfTotalCCU": 20.7
    }
  ],
  "lastUpdated": "2025-01-20T10:00:00Z"
}
```

---

### Get Weekday Stats

Get average concurrent player counts by day of week.

```
GET /api/stats/weekdays
```

#### Example Request

```bash
curl "https://api.fncreate.gg/api/stats/weekdays"
```

#### Example Response

```json
{
  "weekdays": [
    { "day": "Monday", "avgCCU": 2200000 },
    { "day": "Tuesday", "avgCCU": 2150000 },
    { "day": "Wednesday", "avgCCU": 2180000 },
    { "day": "Thursday", "avgCCU": 2250000 },
    { "day": "Friday", "avgCCU": 2650000 },
    { "day": "Saturday", "avgCCU": 3200000 },
    { "day": "Sunday", "avgCCU": 3100000 }
  ],
  "peakDay": "Saturday",
  "lowDay": "Tuesday"
}
```

---

### Get Mode Distribution Stats

Get game mode distribution statistics.

```
GET /api/stats/modes
```

#### Example Request

```bash
curl "https://api.fncreate.gg/api/stats/modes"
```

#### Example Response

```json
{
  "epicVsUGC": {
    "epic": { "mapCount": 50, "totalCCU": 800000, "percent": 28.6 },
    "ugc": { "mapCount": 249950, "totalCCU": 2000000, "percent": 71.4 }
  },
  "buildVsZeroBuild": {
    "build": { "mapCount": 180000, "totalCCU": 1800000, "percent": 64.3 },
    "zeroBuild": { "mapCount": 70000, "totalCCU": 1000000, "percent": 35.7 }
  },
  "rankedVsNonRanked": {
    "ranked": { "mapCount": 25, "totalCCU": 450000, "percent": 16.1 },
    "nonRanked": { "mapCount": 249975, "totalCCU": 2350000, "percent": 83.9 }
  },
  "lastUpdated": "2025-01-20T10:00:00Z"
}
```

---

## Error Handling

All endpoints return errors in a consistent format:

### Error Response Format

```json
{
  "error": "Error message describing what went wrong",
  "details": "Additional details (development only)"
}
```

### Common HTTP Status Codes

| Code | Description |
|------|-------------|
| `200` | Success |
| `400` | Bad Request - Invalid parameters |
| `401` | Unauthorized - Authentication required |
| `404` | Not Found - Resource doesn't exist |
| `429` | Too Many Requests - Rate limit exceeded |
| `500` | Internal Server Error |

### Example Error Responses

**404 Not Found:**
```json
{
  "error": "Map not found"
}
```

**400 Bad Request:**
```json
{
  "error": "Invalid period parameter. Must be one of: 1d, 7d, 1m, 1y, all"
}
```

**429 Rate Limited:**
```json
{
  "error": "Too many requests, please try again later."
}
```

---

## Notes

- All timestamps are in ISO 8601 format (UTC)
- CCU = Concurrent Users (players currently in the map)
- Discovery data is updated every 5-10 minutes
- Historical data retention varies by metric type
- Map codes follow the format `XXXX-XXXX-XXXX`

---

## Support

For API support or questions, visit [fncreate.gg](https://fncreate.gg) or contact the development team.
