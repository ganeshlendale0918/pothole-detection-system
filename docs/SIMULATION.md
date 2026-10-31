# Simulation Lab Documentation

## Purpose
The Simulation & Scenario Lab provides an isolated environment to model hypothetical
road-maintenance scenarios without contaminating real detection records, analytics,
or model evaluation metrics.

## Isolation Guarantee

| Table | Real Data | Simulation Data |
|-------|-----------|-----------------|
| `detections` | ✅ Yes | ❌ NEVER |
| `locations` | ✅ Yes | ❌ NEVER |
| `repair_tasks` | ✅ Yes | ❌ NEVER |
| `simulation_runs` | ❌ NEVER | ✅ Yes |
| `simulation_records` | ❌ NEVER | ✅ Yes |

Simulated records never appear in the Executive Overview, Detection History, Analytics,
GIS Map (real view), Repair Management, or Model Performance pages.

## Configurable Parameters

| Parameter | Range | Description |
|-----------|-------|-------------|
| Number of potholes | 10 – 2,000 | Total simulated detections |
| Detection period | 7 – 90 days | Time window for trend simulation |
| Severity distribution | 0–100% per level | % Low / Medium / High / Critical |
| Geographic areas | Free selection | Which named areas to distribute potholes across |
| Repair capacity | 1 – 50 jobs/day | How many potholes the team can repair per day |
| Repair duration | 1 – 30 days | Average days to complete one repair |
| Budget | 0 – ₹50,000,000 | Total available repair budget |
| Strategy | 4 options | How to prioritise repairs |
| Random seed | 0 – 9,999 | For reproducibility |

## Prioritisation Strategies

| Strategy | Logic |
|----------|-------|
| Priority (Highest Severity First) | Critical → High → Medium → Low |
| Priority (Lowest Cost First) | Cheapest repairs done first (maximises count) |
| Geographic Clustering | Group by area_name (minimises travel) |
| FIFO | Process in detection order |

## Simulation Engine

```
1. Generate N potholes:
   - Severity: sampled from configured distribution
   - Area: randomly selected from configured areas
   - Cost: SEVERITY_COSTS[sev] × uniform(0.8, 1.3)
   - Days to repair: Normal(mean=duration, std=0.3×duration)
   - GPS: Random within India bounding box [SIMULATED — not real coordinates]

2. Apply strategy ordering.

3. Simulate repair progress:
   - Process up to (capacity × duration_days) potholes
   - Subject to budget constraint
   - Mark remaining repairs as "Simulated — Detected" (not repaired)

4. Compute summary statistics.
```

## Output Charts

All charts display prominent **[SIMULATED]** labels:

- Severity distribution donut
- Repair status bar chart
- Daily detection trend area chart
- Area-wise pothole count
- Budget usage pie
- Workload projection narrative

## Saving and Comparing

- Scenarios can be saved to `simulation_runs` (config) and `simulation_records` (potholes)
- Any two saved scenarios can be compared side-by-side
- Individual scenario records can be downloaded as CSV
- Scenarios can be deleted without affecting real data

## Export

- Simulated pothole records: `.csv`
- Scenario summary: `.json`

## Known Limitations

- GPS coordinates are random within India's bounding box — they do not reflect real roads
- Trend simulation is Poisson distributed — simplistic for demonstration purposes
- Repair simulation does not model multi-day travel or team scheduling
- No simulation contamination checks at the UI layer (relying on DB table isolation)
