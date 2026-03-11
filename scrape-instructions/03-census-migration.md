# Task 3: Census ACS Migration / Population Stability

## What You're Getting
One key number per metro area:
- **Geographic mobility rate**: % of population that moved in the past year (from a different county or state)

This feeds into: **Repetition**
Logic: Lower migration = more stable population = same people keep showing up = higher repetition score. This is an INVERSE relationship — low mobility → high score.

## Data Source
**American Community Survey 5-Year Estimates, Table S0701 (Geographic Mobility by Selected Characteristics)**
- API endpoint: `https://api.census.gov/data/2022/acs/acs5/subject`
- No API key required for small queries
- Geographic level: Metropolitan Statistical Area (MSA)

## Exact Steps

### Step 1: Understand the variables
From table S0701:
- `S0701_C01_001E` = Total population 1 year and over
- `S0701_C03_001E` = Moved from different county, same state (count)
- `S0701_C04_001E` = Moved from different state (count)

Migration rate = (S0701_C03_001E + S0701_C04_001E) / S0701_C01_001E

Alternative using table B07001 (Geographic Mobility in the Past Year):
- `B07001_001E` = Total population 1 year and over
- `B07001_065E` = Moved from different county, same state
- `B07001_081E` = Moved from different state

### Step 2: Query the API
Bulk query for all MSAs:
```
https://api.census.gov/data/2022/acs/acs5/subject?get=NAME,S0701_C01_001E,S0701_C03_001E,S0701_C04_001E&for=metropolitan%20statistical%20area/micropolitan%20statistical%20area:*
```

This returns all MSAs at once. Filter down to the 92 markets you need using the same MSA FIPS codes from Task 2 (census-commuting).

### Step 3: Calculate values
For each market:
- `moved_from_diff_county` = S0701_C03_001E
- `moved_from_diff_state` = S0701_C04_001E
- `migration_rate` = (moved_from_diff_county + moved_from_diff_state) / S0701_C01_001E

### Step 4: Handle edge cases
- Same as Task 2: small towns may need county-level data
- Census null marker is -666666666 — skip those
- Use the same MSA-to-market mapping from Task 2

## Output Format
Save as `census-migration-data.json`:
```json
{
  "source": "U.S. Census Bureau, ACS 5-Year Estimates 2022, Table S0701",
  "fetched_date": "2026-03-10",
  "url": "https://api.census.gov/data/2022/acs/acs5/subject",
  "markets": {
    "new-york-ny": {
      "msa_fips": "35620",
      "msa_name": "New York-Newark-Jersey City, NY-NJ-PA",
      "total_population": 19800000,
      "moved_from_diff_county": 250000,
      "moved_from_diff_state": 310000,
      "migration_rate": 0.0283
    },
    "austin-tx": {
      "msa_fips": "12420",
      "msa_name": "Austin-Round Rock-Georgetown, TX",
      "total_population": 2280000,
      "moved_from_diff_county": 68000,
      "moved_from_diff_state": 95000,
      "migration_rate": 0.0715
    }
  }
}
```

## Validation
- All 92 markets should have data
- `migration_rate` should be between 0.01 and 0.15 for US metros
- Spot check: College towns (Ithaca, Athens, Ann Arbor) and boom cities (Austin, Boise) should have HIGHER migration rates. Old stable cities (Pittsburgh, Buffalo, Cleveland) should have LOWER rates.
- NYC should have a moderate rate (~3-4%). Austin/Boise should be higher (~6-8%).
