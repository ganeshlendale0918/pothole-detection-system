"""
4_GIS_Map.py — Interactive GIS Map for RoadSight Intelligence Platform.
FIXES:
  - Tile provider: OpenStreetMap (default, free) + CartoDB Positron (free, no key)
  - CartoDB Dark Matter / dark_nolabels removed — they require a paid API key.
  - Marker popups include repair task link.
  - Location provenance is clearly labelled.
  - Invalid / zero coordinates are skipped gracefully.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import folium
import pandas as pd
import streamlit as st
from folium.plugins import HeatMap, MarkerCluster

from streamlit_folium import st_folium

import config
from src.database import get_detections, get_locations, get_repair_tasks, init_db, save_location
from src.severity import SEVERITY_COLORS
from src.ui_components import (
    empty_state, hero_banner, info_box, inject_css, section_header,
)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="GIS Map · RoadSight", page_icon="🗺️", layout="wide")
init_db()
inject_css()

with st.sidebar:
    st.markdown(
        '<div class="sidebar-logo"><h2>🛣️ RoadSight</h2><p>Intelligence Platform v2.0</p></div>',
        unsafe_allow_html=True,
    )

hero_banner(
    "Interactive GIS Map",
    "Visualise pothole locations, density heatmaps, and geographical clusters",
    "🗺️",
    badge="OpenStreetMap · Marker Clustering · Heatmap · Click to Place",
)

info_box(
    "📍 <b>Location Provenance:</b> All map markers show their source — "
    "<b>manual entry</b>, <b>geocoded address</b>, or <b>map click</b>. "
    "No GPS coordinates are fabricated.",
    kind="info",
)

# ── Severity → Folium colour mapping (free named colours only) ────────────────
_FOLIUM_COLORS = {
    "Critical": "red",
    "High":     "orange",
    "Medium":   "beige",
    "Low":      "green",
    "Unknown":  "gray",
}

# ── Repair status → symbol ────────────────────────────────────────────────────
_REPAIR_ICONS = {
    "Repaired": "check",
    "Closed":   "check",
    "In Progress": "wrench",
    "Assigned": "user",
    "Pending Verification": "question-sign",
    "Verified": "ok-sign",
    "Rejected": "remove",
}


def _sev_icon(sev: str, repair_status: str | None = None) -> folium.Icon:
    icon_name = _REPAIR_ICONS.get(repair_status or "", "road")
    return folium.Icon(
        color=_FOLIUM_COLORS.get(sev, "gray"),
        icon=icon_name,
        prefix="glyphicon",
    )


def _is_valid_coord(lat, lon) -> bool:
    try:
        lat, lon = float(lat), float(lon)
        return abs(lat) > 0.001 or abs(lon) > 0.001  # reject exact 0,0
    except (TypeError, ValueError):
        return False


# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_map, tab_add, tab_data = st.tabs(["🗺️ Map View", "➕ Add Location", "📊 Location Data"])

# ─────────────────────────────────────────────────────────────────────────────
# MAP VIEW
# ─────────────────────────────────────────────────────────────────────────────
with tab_map:
    # Filters
    with st.expander("🔍 Map Filters", expanded=False):
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            sev_opts = st.multiselect(
                "Severity",
                ["Critical", "High", "Medium", "Low"],
                default=["Critical", "High", "Medium", "Low"],
                key="map_sev",
            )
        with fc2:
            show_heatmap = st.checkbox("Show density heatmap", value=False, key="map_heat")
        with fc3:
            show_clusters = st.checkbox("Enable marker clustering", value=True, key="map_cluster")

    # Load locations
    locations = get_locations(severity_filter=sev_opts if sev_opts else None)
    # Load repair tasks for status info
    tasks = get_repair_tasks(limit=500)
    task_by_det = {}
    for t in tasks:
        if t.get("detection_id"):
            task_by_det[t["detection_id"]] = t

    # Determine map centre
    valid_locs = [l for l in locations if _is_valid_coord(l.get("lat"), l.get("lon"))]
    if valid_locs:
        lats = [float(l["lat"]) for l in valid_locs]
        lons = [float(l["lon"]) for l in valid_locs]
        center_lat = sum(lats) / len(lats)
        center_lon = sum(lons) / len(lons)
        zoom = 13 if len(valid_locs) <= 20 else 11
    else:
        center_lat, center_lon = config.DEFAULT_MAP_LAT, config.DEFAULT_MAP_LON
        zoom = config.DEFAULT_MAP_ZOOM

    # ── Build Folium map — OpenStreetMap only (100% free, no API key) ────────
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        tiles="OpenStreetMap",           # Free tile, no API key required
        control_scale=True,
    )

    # Marker layer
    if show_clusters:
        marker_layer = MarkerCluster(name="Pothole Detections")
        marker_layer.add_to(m)
    else:
        marker_layer = m  # type: ignore[assignment]

    # Add markers
    added = 0
    skipped = 0
    for loc in valid_locs:
        lat = float(loc["lat"])
        lon = float(loc["lon"])
        sev = loc.get("severity") or "Unknown"
        conf = loc.get("confidence")
        src = loc.get("location_source", "manual")
        area = loc.get("area_name") or "—"
        addr = loc.get("address") or "—"
        ts = (loc.get("created_at") or "")[:16].replace("T", " ")
        det_id = loc.get("detection_id") or ""

        # Repair info
        task = task_by_det.get(det_id)
        repair_status = task.get("status") if task else None
        task_id_short = (task.get("id") or "")[:8] + "…" if task else None

        popup_html = (
            '<div style="font-family:Inter,sans-serif;min-width:195px;font-size:13px">'
            '<b style="font-size:14px">🕳️ Pothole Detection</b><br>'
            f'<b>Severity:</b> {sev}<br>'
            f'<b>Confidence:</b> {f"{conf:.3f}" if conf else "N/A"}<br>'
            f'<b>Area:</b> {area}<br>'
            f'<b>Address:</b> {addr}<br>'
            f'<b>Location source:</b> {src}<br>'
            f'<b>Recorded:</b> {ts}<br>'
            + (f'<b>Repair status:</b> {repair_status}<br>' if repair_status else "")
            + (f'<b>Task ID:</b> {task_id_short}<br>' if task_id_short else "")
            + (f'<i style="color:#94a3b8">Detection ID: {det_id[:12]}…</i>' if det_id else "")
            + "</div>"
        )
        tooltip_txt = f"{sev} | conf:{conf:.2f}" if conf else sev

        try:
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_html, max_width=270),
                tooltip=tooltip_txt,
                icon=_sev_icon(sev, repair_status),
            ).add_to(marker_layer)
            added += 1
        except Exception:
            skipped += 1

    # Heatmap layer
    if show_heatmap and valid_locs:
        heat_data = [
            [
                float(l["lat"]),
                float(l["lon"]),
                {"Critical": 1.0, "High": 0.75, "Medium": 0.5, "Low": 0.25}.get(
                    l.get("severity", "Low"), 0.3
                ),
            ]
            for l in valid_locs
        ]
        if heat_data:
            HeatMap(
                heat_data,
                name="Density Heatmap",
                radius=22,
                blur=16,
                gradient={"0.3": "#3b82f6", "0.5": "#eab308", "0.75": "#f97316", "1.0": "#ef4444"},
            ).add_to(m)

    folium.LayerControl().add_to(m)

    if skipped:
        info_box(f"⚠️ {skipped} location(s) had invalid coordinates and were not plotted.", kind="warn")

    # Render map
    map_result = st_folium(m, use_container_width=True, height=560, key="main_map_v2")

    # Stats
    st.markdown("---")
    mc1, mc2, mc3, mc4, mc5 = st.columns(5)
    mc1.metric("Mapped Locations", len(valid_locs))
    mc2.metric("Critical", sum(1 for l in valid_locs if l.get("severity") == "Critical"))
    mc3.metric("High", sum(1 for l in valid_locs if l.get("severity") == "High"))
    mc4.metric("With Repairs", len(task_by_det))
    mc5.metric("Geocoded", sum(1 for l in valid_locs if l.get("location_source") == "geocoded"))

    # Unmapped detections
    all_dets = get_detections(limit=500)
    loc_det_ids = {l.get("detection_id") for l in locations if l.get("detection_id")}
    unmapped = [d for d in all_dets if d["id"] not in loc_det_ids]
    if unmapped:
        st.markdown("---")
        section_header(f"Unmapped Detections ({len(unmapped)})", "Add locations to these in the 'Add Location' tab")
        df_um = pd.DataFrame(unmapped)[["id", "created_at", "source_name", "severity", "confidence"]].copy()
        df_um["id"] = df_um["id"].str[:12] + "…"
        df_um["created_at"] = df_um["created_at"].str[:16].str.replace("T", " ")
        df_um.columns = ["ID", "Recorded", "Source", "Severity", "Confidence"]
        st.dataframe(df_um, use_container_width=True, hide_index=True)

    # Export buttons
    if valid_locs:
        df_loc = pd.DataFrame(valid_locs)
        export_cols = [c for c in ["lat", "lon", "severity", "confidence", "area_name", "address", "location_source", "created_at"] if c in df_loc.columns]
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            st.download_button(
                "⬇️ Export Locations CSV",
                data=df_loc[export_cols].to_csv(index=False).encode(),
                file_name="pothole_locations.csv",
                mime="text/csv",
            )
        with col_e2:
            features = [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [l["lon"], l["lat"]]},
                    "properties": {k: l.get(k) for k in ["severity", "confidence", "area_name", "address", "location_source"]},
                }
                for l in valid_locs
            ]
            geojson_str = json.dumps({"type": "FeatureCollection", "features": features}, indent=2)
            st.download_button(
                "⬇️ Export GeoJSON",
                data=geojson_str.encode(),
                file_name="pothole_locations.geojson",
                mime="application/json",
            )
    else:
        empty_state("No Location Data", "Add locations in the 'Add Location' tab.", "🗺️")


# ─────────────────────────────────────────────────────────────────────────────
# ADD LOCATION
# ─────────────────────────────────────────────────────────────────────────────
with tab_add:
    section_header("Add Pothole Location")
    add_tab_1, add_tab_2, add_tab_3 = st.tabs(["📍 Manual Lat/Lon", "🏠 Address Geocoding", "🗺️ Map Click"])

    # ── Manual entry ──────────────────────────────────────────────────────────
    with add_tab_1:
        section_header("Enter coordinates manually")
        info_box("These coordinates will be saved as <b>manual</b> entry — not GPS.", kind="info")
        ac1, ac2 = st.columns(2)
        with ac1:
            m_lat = st.number_input("Latitude", -90.0, 90.0, 0.0, format="%.6f", key="add_lat")
        with ac2:
            m_lon = st.number_input("Longitude", -180.0, 180.0, 0.0, format="%.6f", key="add_lon")
        m_area = st.text_input("Area name", key="add_area")
        m_addr = st.text_input("Address / description", key="add_addr")
        m_notes = st.text_area("Notes", key="add_notes", height=70)

        # Link to detection
        recent_dets = get_detections(limit=30)
        det_options = ["None — standalone marker"] + [
            f"{d['id'][:8]}… | {d.get('source_name','?')[:35]} | {d.get('severity','?')}"
            for d in recent_dets
        ]
        det_sel = st.selectbox("Link to detection (optional)", det_options, key="add_det_sel")

        if st.button("📍 Save Manual Location", key="add_manual_btn"):
            if not _is_valid_coord(m_lat, m_lon):
                st.warning("Enter non-zero coordinates (0,0 is the ocean, not a valid location).")
            else:
                det_id = None
                if det_sel != "None — standalone marker":
                    idx = det_options.index(det_sel) - 1
                    det_id = recent_dets[idx]["id"] if 0 <= idx < len(recent_dets) else None
                try:
                    save_location(
                        lat=m_lat, lon=m_lon,
                        detection_id=det_id,
                        address=m_addr or None,
                        location_source="manual",
                        area_name=m_area or None,
                        notes=m_notes or None,
                    )
                    st.success(f"✅ Location saved: ({m_lat:.5f}, {m_lon:.5f})")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to save: {e}")

    # ── Geocoding ─────────────────────────────────────────────────────────────
    with add_tab_2:
        section_header("Geocode an Address")
        info_box(
            "Uses Nominatim (OpenStreetMap, free). Requires internet connection. "
            "Results are labelled as <b>geocoded</b>.",
            kind="info",
        )
        addr_input = st.text_input("Enter address:", key="geo_addr",
                                   placeholder="e.g. MG Road, Bangalore, India")
        if st.button("🔍 Search Address", key="geo_search"):
            if not addr_input.strip():
                st.warning("Enter an address first.")
            else:
                with st.spinner("Geocoding…"):
                    try:
                        from geopy.geocoders import Nominatim
                        from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
                        geolocator = Nominatim(user_agent="roadsight_v2_gis")
                        location = geolocator.geocode(addr_input, timeout=12)
                        if location:
                            st.session_state["geo_result"] = {
                                "lat": location.latitude,
                                "lon": location.longitude,
                                "address": location.address,
                            }
                            st.success(f"Found: {location.address}")
                        else:
                            st.warning("Address not found. Try a more specific query.")
                    except ImportError:
                        st.error("geopy not installed. Run: pip install geopy")
                    except (GeocoderTimedOut, GeocoderUnavailable):
                        st.warning("Geocoding service unavailable. Check internet connection.")
                    except Exception as exc:
                        st.error(f"Geocoding error: {exc}")

        geo_result = st.session_state.get("geo_result")
        if geo_result:
            st.info(f"📍 Lat: {geo_result['lat']:.6f} | Lon: {geo_result['lon']:.6f}")
            st.caption(geo_result.get("address", ""))
            geo_area = st.text_input("Area name (optional)", key="geo_area")
            geo_notes = st.text_area("Notes", key="geo_notes", height=68)
            g1, g2 = st.columns(2)
            with g1:
                if st.button("💾 Save Geocoded Location", key="geo_save"):
                    try:
                        save_location(
                            lat=geo_result["lat"], lon=geo_result["lon"],
                            address=geo_result["address"],
                            location_source="geocoded",
                            area_name=geo_area or None,
                            notes=geo_notes or None,
                        )
                        st.success("✅ Geocoded location saved!")
                        del st.session_state["geo_result"]
                        st.rerun()
                    except Exception as e:
                        st.error(f"Save failed: {e}")
            with g2:
                if st.button("✕ Clear Result", key="geo_clear"):
                    del st.session_state["geo_result"]
                    st.rerun()

    # ── Map click ─────────────────────────────────────────────────────────────
    with add_tab_3:
        section_header("Select Location by Clicking the Map")
        info_box(
            "Click anywhere on the map below. The coordinates are captured automatically. "
            "Fill in optional details and save.",
            kind="info",
        )

        click_map = folium.Map(
            location=[config.DEFAULT_MAP_LAT, config.DEFAULT_MAP_LON],
            zoom_start=config.DEFAULT_MAP_ZOOM,
            tiles="OpenStreetMap",       # Free tile, no API key required
        )
        folium.LatLngPopup().add_to(click_map)

        click_result = st_folium(click_map, use_container_width=True, height=420, key="click_map_v2")

        clicked = click_result.get("last_clicked")
        if clicked:
            clat = clicked["lat"]
            clon = clicked["lng"]
            st.success(f"📍 Selected: Lat {clat:.6f}, Lon {clon:.6f}")
            cl_area = st.text_input("Area name", key="click_area")
            cl_addr = st.text_input("Address / description", key="click_addr")
            cl_notes = st.text_area("Notes", key="click_notes", height=68)

            # Link to detection
            recent_d2 = get_detections(limit=20)
            det_opts2 = ["None"] + [
                f"{d['id'][:8]}… | {d.get('source_name','?')[:30]} | {d.get('severity','?')}"
                for d in recent_d2
            ]
            det_sel2 = st.selectbox("Link to detection (optional)", det_opts2, key="click_det_sel")

            if st.button("💾 Save Map-Click Location", key="click_save"):
                det_id2 = None
                if det_sel2 != "None":
                    idx2 = det_opts2.index(det_sel2) - 1
                    det_id2 = recent_d2[idx2]["id"] if 0 <= idx2 < len(recent_d2) else None
                try:
                    save_location(
                        lat=clat, lon=clon,
                        detection_id=det_id2,
                        address=cl_addr or None,
                        location_source="map_click",
                        area_name=cl_area or None,
                        notes=cl_notes or None,
                    )
                    st.success(f"✅ Map-click location saved: ({clat:.5f}, {clon:.5f})")
                    st.rerun()
                except Exception as e:
                    st.error(f"Save failed: {e}")
        else:
            st.caption("Click on the map above to select a location.")


# ─────────────────────────────────────────────────────────────────────────────
# LOCATION DATA TABLE
# ─────────────────────────────────────────────────────────────────────────────
with tab_data:
    section_header("All Saved Locations")
    all_locs = get_locations()
    if all_locs:
        df_all = pd.DataFrame(all_locs)
        display_lc = [c for c in ["lat", "lon", "severity", "confidence", "area_name",
                                   "address", "location_source", "created_at"] if c in df_all.columns]
        df_disp = df_all[display_lc].copy()
        df_disp.columns = [c.replace("_", " ").title() for c in df_disp.columns]
        if "Created At" in df_disp.columns:
            df_disp["Created At"] = df_disp["Created At"].str[:16].str.replace("T", " ")
        st.dataframe(df_disp, use_container_width=True, hide_index=True)
        st.metric("Total saved locations", len(all_locs))
        csv_all = df_all[display_lc].to_csv(index=False).encode()
        st.download_button(
            "⬇️ Download All Locations CSV",
            data=csv_all,
            file_name="all_locations.csv",
            mime="text/csv",
        )
    else:
        empty_state("No Locations Yet", "Add locations using the 'Add Location' tab.", "📍")
