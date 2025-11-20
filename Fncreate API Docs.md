# fncreate.gg API Documentation

A simple proxy API for the fn360.gg Fortnite Creative API with built-in caching and no authentication required.

**Base URL:** `https://fncreate.gg`

---

## 📋 Table of Contents
- [Maps Endpoints](#maps-endpoints)
- [Discovery Endpoints](#discovery-endpoints)
- [Creator Endpoints](#creator-endpoints)
- [Status Endpoints](#status-endpoints)
- [Caching](#caching)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)

---

## 🗺️ Maps Endpoints

### Get All Maps
Returns a paginated list of Fortnite Creative maps.

**Endpoint:** `GET /api/maps`

**Query Parameters:**
- `page` (optional) - Page number for pagination (default: 1)
- `noepic` (optional) - Exclude Epic Games maps (`true`/`false`)

**Example Request:**
```bash
curl https://fncreate.gg/api/maps?page=1&noepic=true
```

**Example Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "8530-0110-2817",
      "name": "🍌PEELY VS JONESY🦸‍♂️",
      "image_url": "https://cdn-0001.qstv.on.epicgames.com/...",
      "introduction": "🆕 Play with ALL NEW Chapter 6 Weapons",
      "tagline": "🆕 Play with ALL NEW Chapter 6 Weapons...",
      "tags": ["pvp", "team deathmatch", "practice", "action"],
      "ccu_record": 23870,
      "lastSyncCcu": 606,
      "owner_code": "natmor",
      "owner_name": "NATM0R"
    }
    // ... 19 more maps
  ],
  "timestamp": "2025-11-19T18:00:00.000Z"
}
```

**Pagination:** Returns 20 maps per page.

---

### Get Map Details
Get detailed information about a specific map by its mnemonic code.

**Endpoint:** `GET /api/maps/{mnemonic}`

**Path Parameters:**
- `mnemonic` - The map code (e.g., `8530-0110-2817`)

**Query Parameters:**
- `cs` (optional) - Include creator statistics (`true`/`false`)

**Example Request:**
```bash
curl https://fncreate.gg/api/maps/8530-0110-2817?cs=true
```

**Example Response:**
```json
{
  "success": true,
  "data": {
    "id": "8530-0110-2817",
    "name": "🍌PEELY VS JONESY🦸‍♂️",
    "ccu_record": 23870,
    "ccu_record_date": "2025-08-27T18:00:00.000Z",
    "lastSyncCcu": 606,
    "lastSyncDate": "2025-11-18T20:57:00.000Z",
    "image_url": "https://cdn-0001.qstv.on.epicgames.com/...",
    "introduction": "🆕 Play with ALL NEW Chapter 6 Weapons",
    "tagline": "🆕 Play with ALL NEW Chapter 6 Weapons...",
    "tags": ["pvp", "team deathmatch", "practice", "action"],
    "max_players": 20,
    "minutes_played": 187188756,
    "owner_code": "natmor",
    "owner_name": "NATM0R",
    "published": "2024-08-23T15:59:25.690Z",
    "version": 255,
    "xp_enabled": true,
    "creator": {
      "id": "natmor",
      "name": "NATM0R",
      "lookup_display_name": "natmor",
      "lookup_follower_count": 387585,
      "lookup_bio": "👇👇👇LIKE 👇👇👇",
      "lookup_avatar": "https://cdn-0001.qstv.on.epicgames.com/...",
      "last_sync_ccu": 367
    }
  },
  "timestamp": "2025-11-19T18:00:00.000Z"
}
```

---

### Get Map Changelog
Get version history and changelog for a specific map.

**Endpoint:** `GET /api/maps/{mnemonic}/changelog`

**Path Parameters:**
- `mnemonic` - The map code (e.g., `8530-0110-2817`)

**Example Request:**
```bash
curl https://fncreate.gg/api/maps/8530-0110-2817/changelog
```

**Example Response:**
```json
{
  "success": true,
  "data": [
    {
      "version": 255,
      "published": "2025-11-15T12:30:00.000Z",
      "changes": "Updated weapons for Chapter 6"
    }
    // ... more versions
  ],
  "timestamp": "2025-11-19T18:00:00.000Z"
}
```

---

### Get Map Discovery Data
Get discovery-related information about a map.

**Endpoint:** `GET /api/maps/{mnemonic}/discovery`

**Path Parameters:**
- `mnemonic` - The map code (e.g., `8530-0110-2817`)

**Example Request:**
```bash
curl https://fncreate.gg/api/maps/8530-0110-2817/discovery
```

---

### Get Map Statistics
Get detailed statistics for a specific map over a time period.

**Endpoint:** `POST /api/maps/{mnemonic}/v2/stats`

**Path Parameters:**
- `mnemonic` - The map code (e.g., `8530-0110-2817`)

**Request Body:**
```json
{
  "type": "24h"
}
```

**Type Options:** `24h`, `7d`, `30d`, `all`

**Example Request:**
```bash
curl -X POST https://fncreate.gg/api/maps/8530-0110-2817/v2/stats \
  -H "Content-Type: application/json" \
  -d '{"type":"24h"}'
```

**Example Response:**
```json
{
  "success": true,
  "data": {
    "id": "8530-0110-2817",
    "period": "24h",
    "avg_ccu": 550,
    "peak_ccu": 850,
    "total_plays": 12500,
    "unique_players": 8300
  },
  "timestamp": "2025-11-19T18:00:00.000Z"
}
```

---

### Get Total Maps Statistics
Get aggregate statistics for all maps.

**Endpoint:** `GET /api/maps/total/stats/latest`

**Example Request:**
```bash
curl https://fncreate.gg/api/maps/total/stats/latest
```

**Example Response:**
```json
{
  "success": true,
  "data": {
    "total_maps": 450000,
    "total_ccu": 2500000,
    "total_plays": 95000000000
  },
  "timestamp": "2025-11-19T18:00:00.000Z"
}
```

---

### Get Total Maps V2 Statistics
Get aggregate statistics for all maps with time period.

**Endpoint:** `POST /api/maps/total/v2/stats`

**Request Body:**
```json
{
  "id": "total",
  "type": "24h"
}
```

**Type Options:** `24h`, `7d`, `30d`, `all`

**Example Request:**
```bash
curl -X POST https://fncreate.gg/api/maps/total/v2/stats \
  -H "Content-Type: application/json" \
  -d '{"id":"total","type":"7d"}'
```

**Example Response:**
```json
{
  "success": true,
  "data": {
    "period": "7d",
    "total_maps": 450000,
    "avg_ccu": 2350000,
    "peak_ccu": 3100000
  },
  "timestamp": "2025-11-20T18:00:00.000Z"
}
```

---

## 🔍 Discovery Endpoints

### Get Discovery Surface
Get maps featured in the Fortnite Creative discovery surface.

**Endpoint:** `GET /api/discovery/surface`

**Query Parameters:**
- `date` (optional) - Date or `latest` (default: `latest`)
- `surface` (optional) - Surface type (e.g., `CreativeDiscoverySurface_Browse`)

**Example Request:**
```bash
curl https://fncreate.gg/api/discovery/surface?date=latest&surface=CreativeDiscoverySurface_Browse
```

**Example Response:**
```json
{
  "success": true,
  "data": {
    "date": "2025-11-19",
    "surface": "CreativeDiscoverySurface_Browse",
    "panels": [
      {
        "panel_name": "Featured",
        "maps": [...]
      }
    ]
  },
  "timestamp": "2025-11-19T18:00:00.000Z"
}
```

---

### Get Discovery Top Experiences
Get top experiences from discovery panels.

**Endpoint:** `GET /api/discovery/top`

**Query Parameters:**
- `date` (optional) - Date or `latest` (default: `latest`)
- `panel` (optional) - Panel name (default: `Experiences_ByEpic_Flat`)

**Example Request:**
```bash
curl https://fncreate.gg/api/discovery/top?date=latest&panel=Experiences_ByEpic_Flat
```

---

## 👤 Creator Endpoints

### Get All Creators
Get a paginated list of creators.

**Endpoint:** `GET /api/creators`

**Query Parameters:**
- `page` (optional) - Page number for pagination (default: 1)

**Example Request:**
```bash
curl https://fncreate.gg/api/creators?page=2
```

**Example Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "natmor",
      "name": "NATM0R",
      "lookup_display_name": "natmor",
      "lookup_follower_count": 387585,
      "lookup_bio": "👇👇👇LIKE 👇👇👇",
      "last_sync_ccu": 367,
      "last_sync_minutes_played": 224539843
    }
    // ... more creators
  ],
  "timestamp": "2025-11-19T18:00:00.000Z"
}
```

**Pagination:** Returns 25 creators per page.

---

## ⚡ Status Endpoints

### Get Server Status
Check the status of Fortnite servers.

**Endpoint:** `GET /api/external/server_status`

**Example Request:**
```bash
curl https://fncreate.gg/api/external/server_status
```

**Example Response:**
```json
{
  "success": true,
  "data": {
    "last_valid_status": "UP",
    "last_valid_status_date": "2025-11-19T18:00:00.000Z",
    "last_valid_status_message": "Fortnite is Online"
  },
  "timestamp": "2025-11-19T18:00:00.000Z"
}
```

---

### Health Check
Simple health check endpoint.

**Endpoint:** `GET /health`

**Example Request:**
```bash
curl https://fncreate.gg/health
```

**Example Response:**
```json
{
  "status": "ok",
  "service": "fn360-proxy",
  "timestamp": "2025-11-19T18:00:00.000Z"
}
```

---

### Clear Cache
Clear all cached API responses.

**Endpoint:** `POST /api/cache/clear`

**Example Request:**
```bash
curl -X POST https://fncreate.gg/api/cache/clear
```

**Example Response:**
```json
{
  "success": true,
  "message": "Cleared 150 cache entries",
  "count": 150
}
```

---

## 💾 Caching

All API responses are automatically cached in Redis to improve performance and reduce load on the upstream fn360.gg API.

**Cache TTLs (Time To Live):**
- Map details: **10 minutes** (600s)
- Map changelogs: **30 minutes** (1800s)
- Discovery data: **10 minutes** (600s)
- Map statistics: **5 minutes** (300s)
- All maps list: **3 minutes** (180s)
- Creators list: **10 minutes** (600s)
- Server status: **1 minute** (60s)

**Cache Keys:**
Cached responses include query parameters, so `?page=1` and `?page=2` are cached separately.

---

## ❌ Error Handling

All endpoints follow a consistent error response format:

**Error Response:**
```json
{
  "success": false,
  "error": "Error message",
  "details": {
    // Additional error details if available
  }
}
```

**Common HTTP Status Codes:**
- `200` - Success
- `400` - Bad Request (invalid parameters)
- `404` - Not Found (map/resource doesn't exist)
- `500` - Internal Server Error
- `502` - Bad Gateway (fn360.gg API unavailable)
- `503` - Service Unavailable

---

## 🚦 Rate Limiting

Currently, **rate limiting is disabled** for this API. All requests are allowed.

---


## 🔗 Quick Reference

```bash
# Get maps with pagination
curl https://fncreate.gg/api/maps?page=5&noepic=true

# Get specific map details
curl https://fncreate.gg/api/maps/8530-0110-2817?cs=true

# Get map stats
curl -X POST https://fncreate.gg/api/maps/8530-0110-2817/v2/stats \
  -H "Content-Type: application/json" \
  -d '{"type":"24h"}'

# Get total maps stats
curl -X POST https://fncreate.gg/api/maps/total/v2/stats \
  -H "Content-Type: application/json" \
  -d '{"id":"total","type":"7d"}'

# Get creators
curl https://fncreate.gg/api/creators?page=1

# Get server status
curl https://fncreate.gg/api/external/server_status

# Health check
curl https://fncreate.gg/health
```

---

**Last Updated:** November 19, 2025
