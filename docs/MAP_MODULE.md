# GIS Map Module Documentation

## Overview
The GIS Map page provides an interactive Folium-based map showing all pothole locations
with saved coordinates. Locations can be added by address, manual coordinates, or map click.

## Location Sources

All location records include a `location_source` field indicating data provenance:

| Source Value | Meaning | Labelled As |
|-------------|---------|-------------|
| `manual` | User entered lat/lon manually | "Manual Entry" (blue info icon) |
| `map_click` | User clicked on the map | "Map Selection" (finger pointer icon) |
| `geocoded` | Address resolved via Nominatim | "Geocoded Address" (search icon) |
| `gps` | GPS coordinates from field device | "GPS Reading" (satellite icon) |

**GPS fabrication is strictly prohibited.** No GPS coordinates are generated automatically
by the platform. Field GPS (`gps` source) must be entered explicitly by the operator.

## Adding Locations

### Method 1: Address Geocoding
1. Enter a street address in the text field.
2. Click **Geocode Address**.
3. The app calls geopy/Nominatim to resolve coordinates.
4. Confirm the result before saving.
5. Optionally link to an existing detection record.
6. Source type saved as `geocoded`.

**Requirements:** Internet connection. Subject to Nominatim rate limits (1 req/sec).

### Method 2: Manual Coordinates
1. Enter latitude and longitude directly.
2. Source type saved as `manual`.

### Method 3: Map Click
1. The map's "Draw" tool or click-handler captures coordinates.
2. Source type saved as `map_click`.

## Filtering

The map supports filtering by:
- Severity (Critical / High / Medium / Low)
- Date range
- Location source type
- Area name

## Marker Colours

| Severity | Marker Colour |
|----------|--------------|
| Critical | 🔴 Red |
| High | 🟠 Orange |
| Medium | 🟡 Yellow/Beige |
| Low | 🟢 Green |
| Unknown | 🔵 Blue |

## Heatmap

Toggling the heatmap overlays a density gradient using all mapped coordinates,
showing geographic concentration of pothole reports.

## Marker Clustering

MarkerCluster is enabled by default. Clusters expand on zoom.
Disable via the map controls if needed.

## Export

From the map page:
- **CSV:** All location records with lat/lon, area name, severity, source type
- **GeoJSON:** FeatureCollection with point geometry and all properties

## Database Schema

```sql
CREATE TABLE locations (
    id              TEXT PRIMARY KEY,
    detection_id    TEXT,            -- FK → detections.id (nullable)
    created_at      TEXT NOT NULL,
    lat             REAL NOT NULL,
    lon             REAL NOT NULL,
    address         TEXT,
    location_source TEXT NOT NULL DEFAULT 'manual',
    area_name       TEXT,
    notes           TEXT
);
```

## Geocoding Configuration

Geocoding is enabled/disabled in **Settings → Map → Enable Address Geocoding**.
Can also be disabled at module level by setting `geocoding_enabled = false` in app_settings.

When disabled, only manual coordinate and map-click entry are available.
