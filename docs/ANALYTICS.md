# Analytics Module Documentation

## Overview
The Advanced Analytics page provides interactive Plotly charts derived exclusively
from real detection and repair records in the SQLite database.

## Data Sources

All data is fetched from the live database. No hardcoded values or fabricated trends.
Empty states are shown when no data is available for a metric.

## Chart Inventory

### Detection Trends
| Chart | Description |
|-------|-------------|
| Daily Detection Count | Bar chart — detections per day in selected date range |
| Daily Detection by Severity | Stacked bar chart — breakdown by severity level per day |

### Confidence Analysis
| Chart | Description |
|-------|-------------|
| Confidence Score Distribution | Histogram of all detection confidence values |
| Confidence vs Area Ratio | Scatter (coloured by severity) — bounding box size vs confidence |

### Geographic Analysis
| Chart | Description |
|-------|-------------|
| Potholes by Area (Top 15) | Horizontal bar chart — count per area_name from locations |

### Repair Analytics
| Chart | Description |
|-------|-------------|
| Repair Status Distribution | Donut chart — task count per status |
| Repair Tasks by Priority | Bar chart — task count per priority |
| Estimated vs Actual Cost | Scatter (coloured by priority) — cost comparison |

## Filters

- **Date Range:** Applied to detection queries (from/to)
- **Severity Multi-select:** Available on some charts
- **Interactive Plotly Legends:** Click to toggle series

## Exports

| Export | Format | Contents |
|--------|--------|----------|
| Daily CSV | CSV | Daily detection counts |
| Repair Tasks CSV | CSV | All repair task fields |
| Full Analytics Export | Excel | Detections + Repair Tasks (two sheets) |

## Empty State Handling

Every chart includes an empty-state fallback:
- Shown when the queried dataset contains no records
- Includes a descriptive message explaining what data is needed
- No error is raised — the chart container gracefully degrades

## Performance Notes

- Detection queries default to 5,000 row limit for analytics
- Repair task queries default to 2,000 row limit
- `@st.cache_data` is NOT used on analytics queries because data changes frequently
- For very large databases (>50,000 records), consider adding date range pre-filters

## Adding New Charts

1. Add a database query function to `src/database.py` returning `List[dict]`
2. In `pages/7_Advanced_Analytics.py`, load the data after the existing queries
3. Create a Plotly figure with `template="plotly_dark"` and `paper_bgcolor="rgba(0,0,0,0)"`
4. Wrap in an `if not df.empty` block with `empty_state(...)` fallback
5. Add a download button if the data is exportable
