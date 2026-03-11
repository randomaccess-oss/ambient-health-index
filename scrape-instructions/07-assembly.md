# Task 7: Assembly — Merge Raw Data into Scored markets.json

## What This Task Does
Takes the 6 raw data files from Tasks 1–6 and produces the final `markets.json` with 0–100 scores for each condition, plus auto-generated notes.

## Input Files
You need all 6 files:
1. `walkscore-data.json` (Walk Score + Transit Score per city)
2. `census-commuting-data.json` (commute rate + mean commute time per MSA)
3. `census-migration-data.json` (migration rate per MSA)
4. `census-cbp-data.json` (bar counts + per capita density per MSA)
5. `census-density-data.json` (population density per MSA)
6. `niaaa-consumption-data.json` (per-capita alcohol consumption per state)

## Scoring Formulas

### Temporal Synchronization (0–100)
Inputs: `commute_rate`, `mean_commute_minutes`
```
commute_component = normalize(commute_rate, min=0.70, max=0.95) * 100
    → 0.70 or below = 0, 0.95 or above = 100

commute_time_component = normalize_inverse(mean_commute_minutes, min=15, max=40) * 100
    → 15 min or below = 100, 40 min or above = 0
    → Inverse because SHORTER commute = better sync (people arrive more reliably)

temporal_score = round(commute_component * 0.6 + commute_time_component * 0.4)
```

### Spatial Concentration (0–100)
Inputs: `walk_score`, `msa_density_per_sqmi` (or `urban_density_per_sqmi`), `bars_per_10k`
```
walk_component = walk_score  (already 0–100)

density_component = normalize(urban_density_per_sqmi, min=500, max=5500) * 100
    → If urban_density not available, use: normalize(msa_density_per_sqmi, min=50, max=3000) * 100

bar_density_component = normalize(bars_per_10k, min=0.5, max=5.0) * 100

spatial_score = round(walk_component * 0.4 + density_component * 0.3 + bar_density_component * 0.3)
```

### Low Planning Cost (0–100)
Inputs: `transit_score`, `bars_per_10k`
```
transit_component = transit_score  (already 0–100, use 0 if null)

bar_density_component = normalize(bars_per_10k, min=0.5, max=5.0) * 100

If transit_score is not null:
    planning_score = round(transit_component * 0.5 + bar_density_component * 0.5)
Else (no transit data — small cities):
    planning_score = round(bar_density_component * 0.7 + 15)
    → Small cities get a small baseline bump (walking distance in small towns is easy)
    → Cap at 100
```

### Social Permission (0–100)
Inputs: `total_ethanol_gallons` (state level), `bars_per_10k` (metro level)
```
consumption_component = normalize(total_ethanol_gallons, min=1.5, max=4.0) * 100
    → 1.5 gal or below = 0, 4.0 gal or above = 100

bar_culture_component = normalize(bars_per_10k, min=0.5, max=5.0) * 100

permission_score = round(consumption_component * 0.5 + bar_culture_component * 0.5)
```

### Repetition (0–100)
Inputs: `migration_rate`
```
stability_component = normalize_inverse(migration_rate, min=0.02, max=0.10) * 100
    → 0.02 or below = 100 (very stable), 0.10 or above = 0 (very transient)
    → INVERSE: low migration = high repetition

repetition_score = round(stability_component)
```

### Normalize function
```
normalize(value, min, max):
    if value <= min: return 0
    if value >= max: return 1
    return (value - min) / (max - min)

normalize_inverse(value, min, max):
    return 1 - normalize(value, min, max)
```

## Auto-Generated Notes
For each condition, generate a short descriptive note (1 sentence) based on the raw data. Examples:

**Temporal:**
- If commute_rate > 0.88: "[City] has strong commuter presence with [X]% of workers commuting"
- If commute_rate < 0.78: "High remote-work adoption reduces synchronized arrivals"
- Include mean commute time: "Average [X]-minute commute"

**Spatial:**
- Reference Walk Score: "Walk Score of [X]"
- Reference bar density: "[X] bars per 10K residents"
- If density is high: "Dense urban core"
- If density is low: "Spread-out metro with limited walkable corridors"

**Planning:**
- If transit_score > 60: "Strong transit (score [X]) makes spontaneous outings easy"
- If transit_score is null or low: "Car-dependent, but [X] bars per 10K keeps options accessible"
- If bars_per_10k > 3: "High venue density means a bar is always nearby"

**Permission:**
- Reference state consumption: "[State] ranks [high/moderate/low] in per-capita consumption ([X] gal)"
- If bars_per_10k high: "Strong on-premise drinking culture"
- If Utah or low-consumption state: "More conservative drinking norms"

**Repetition:**
- If migration_rate < 0.03: "Very stable population — low turnover keeps regulars coming back"
- If migration_rate > 0.07: "High population churn makes building repeat crowds harder"
- Reference specific rate: "[X]% of residents moved from outside the area last year"

## Output Format
Produce the final `markets.json` matching this exact schema:
```json
{
  "meta": {
    "version": "2.0.0",
    "generated": "2026-03-10",
    "sources": "Walk Score, U.S. Census ACS 2022, Census CBP 2022, NIAAA Surveillance Report",
    "method": "Normalized scoring from public data sources — see scrape-instructions/ for methodology"
  },
  "markets": [
    {
      "id": "new-york-ny",
      "city": "New York",
      "state": "NY",
      "region": "Northeast",
      "populationTier": "Mega",
      "conditions": {
        "temporal": {
          "score": 72,
          "note": "Strong commuter culture (87% commute rate), but long 37-min average commute"
        },
        "spatial": {
          "score": 93,
          "note": "Walk Score 88, 2.1 bars per 10K, highest urban density in the US"
        },
        "planning": {
          "score": 88,
          "note": "Excellent transit (score 89) and high venue density make planning unnecessary"
        },
        "permission": {
          "score": 76,
          "note": "NY ranks above average in consumption (2.76 gal), strong on-premise culture"
        },
        "repetition": {
          "score": 81,
          "note": "Relatively stable population (2.8% migration rate) for a city this size"
        }
      }
    }
  ]
}
```

## Important Rules
1. Keep the same 92 markets with the same `id`, `city`, `state`, `region`, `populationTier` from the current markets.json
2. Only replace `conditions` (scores + notes)
3. All scores must be integers 0–100
4. All notes must be 1 sentence, referencing specific data points
5. Update `meta.version` to "2.0.0" and `meta.sources` to list actual sources used
6. If a market is missing data for any input, flag it in the note (e.g., "Transit Score unavailable; estimated from bar density only")

## Validation
After assembly:
- 92 markets, each with 5 conditions, each condition has score (int 0–100) and note (string)
- No null scores
- Score distribution should roughly follow: some clustering around 40–70, with outliers at both ends
- Top spatial scores: NYC, SF, Boston, Chicago
- Top permission scores: Markets in WI, NV, DC, LA
- Lowest permission: UT markets (Salt Lake City, Park City)
- Top repetition: Old/stable cities (Pittsburgh, Buffalo, Cleveland)
- Lowest repetition: Boom cities (Austin, Boise, Nashville)
