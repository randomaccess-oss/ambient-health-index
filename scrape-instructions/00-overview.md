# Ambient Health Index — Data Scrape Instructions

## Goal
Pull real data for 92 U.S. markets to score them across 5 conditions (0–100 scale).
Each task below is self-contained. Run them independently on separate machines if needed.
Each task outputs a single JSON file. A final assembly step merges them into `markets.json`.

## Market List
The 92 markets are defined in `markets.json` in this repo. Each market has:
- `id` (e.g., "new-york-ny")
- `city` (e.g., "New York")
- `state` (e.g., "NY")
- `region` (e.g., "Northeast")
- `populationTier` (e.g., "Mega")

## Tasks
1. **Walk Score + Transit Score** → `walkscore-data.json`
2. **Census ACS Commuting** → `census-commuting-data.json`
3. **Census ACS Migration** → `census-migration-data.json`
4. **Census CBP Bar/Restaurant Counts** → `census-cbp-data.json`
5. **Census Population Density** → `census-density-data.json`
6. **NIAAA Alcohol Consumption** → `niaaa-consumption-data.json`
7. **Assembly** → merge all 6 files into scored `markets.json`

## Output Format (per task)
Each task outputs a JSON file shaped like:
```json
{
  "source": "Name of source",
  "fetched_date": "YYYY-MM-DD",
  "url": "URL where data was pulled from",
  "markets": {
    "new-york-ny": { ... raw values ... },
    "chicago-il": { ... raw values ... }
  }
}
```

## Condition Mapping (for assembly step)
| Condition | Inputs |
|---|---|
| Temporal Synchronization | Census ACS commuting rate, mean commute time |
| Spatial Concentration | Walk Score, Census density, CBP bar count per capita |
| Planning Cost | Transit Score, CBP bar density per capita |
| Social Permission | NIAAA per-capita consumption, CBP on-premise count per capita |
| Repetition | Census ACS migration rate (inverse — lower migration = higher score) |
