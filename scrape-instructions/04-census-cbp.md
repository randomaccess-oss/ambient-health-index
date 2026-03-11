# Task 4: Census County Business Patterns — Bar/Restaurant Counts

## What You're Getting
Per metro area:
- **Number of drinking place establishments** (NAICS 7224)
- **Number of food service & drinking establishments** (NAICS 722) — broader category
- **Population** (to calculate per-capita density)

These feed into:
- **Spatial Concentration** (bar density per capita — more bars = more concentrated)
- **Planning Cost** (bar density per capita — more bars = easier to find one spontaneously)
- **Social Permission** (on-premise density — more bars = more social acceptance of drinking)

## Data Source
**Census Bureau County Business Patterns (CBP)**
- API endpoint: `https://api.census.gov/data/2022/cbp`
- No API key required for small queries
- Geographic level: County (aggregate to MSA) or MSA directly

## Exact Steps

### Step 1: Understand the variables and NAICS codes
- NAICS `7224` = Drinking Places (Alcoholic Beverages) — this is BARS specifically
- NAICS `7225` = Restaurants and Other Eating Places
- NAICS `722` = Food Services and Drinking Places (parent category)

CBP variables:
- `ESTAB` = Number of establishments
- `EMP` = Number of employees (useful secondary metric)
- `NAICS2017` = NAICS code to filter by

### Step 2: Query the API
For all counties, NAICS 7224 (Drinking Places):
```
https://api.census.gov/data/2022/cbp?get=NAME,ESTAB,EMP,NAICS2017&for=county:*&NAICS2017=7224
```

For all counties, NAICS 722 (broader food services):
```
https://api.census.gov/data/2022/cbp?get=NAME,ESTAB,EMP,NAICS2017&for=county:*&NAICS2017=722
```

NOTE: If the 2022 CBP data isn't available yet, try 2021:
```
https://api.census.gov/data/2021/cbp?get=NAME,ESTAB,EMP,NAICS2017&for=county:*&NAICS2017=7224
```

### Step 3: Map counties to markets
Each MSA is made up of counties. You need to:
1. Get the county-to-MSA mapping from the Census delineation files (same file as Task 2)
2. Sum `ESTAB` across all counties in each MSA
3. Match MSAs to the 92 market IDs

For cities that are also counties (e.g., "New York" = 5 boroughs/counties in NYC), sum all relevant counties.

For small markets not in an MSA (Marfa TX, Telluride CO, etc.), just use the single county.

County FIPS format: State FIPS (2 digits) + County FIPS (3 digits)
- Example: New York County, NY = state 36, county 061 → "36061"

### Step 4: Get population for per-capita calculation
You'll need MSA population to calculate bars per capita. You can get this from ACS:
```
https://api.census.gov/data/2022/acs/acs5?get=NAME,B01001_001E&for=metropolitan%20statistical%20area/micropolitan%20statistical%20area:*
```
Where `B01001_001E` = total population.

### Step 5: Calculate values
For each market:
- `drinking_places` = sum of ESTAB where NAICS = 7224 across all counties in the MSA
- `food_and_drinking` = sum of ESTAB where NAICS = 722 across all counties in the MSA
- `population` = MSA population from ACS
- `bars_per_10k` = (drinking_places / population) * 10000
- `food_drink_per_10k` = (food_and_drinking / population) * 10000

### Step 6: Handle edge cases
- Some very small counties may have data suppressed (shown as null or 0) for confidentiality. The CBP suppresses data when there are very few establishments. Note these cases.
- NAICS 7224 can be sparse in small markets. If a market shows 0 drinking places, it probably means data is suppressed, not that there are literally no bars. Flag these for manual review.
- The CBP may use NAICS2017 or NAICS2022 depending on the data year. Try both if one doesn't work.

## Output Format
Save as `census-cbp-data.json`:
```json
{
  "source": "U.S. Census Bureau, County Business Patterns 2022",
  "fetched_date": "2026-03-10",
  "url": "https://api.census.gov/data/2022/cbp",
  "markets": {
    "new-york-ny": {
      "msa_fips": "35620",
      "msa_name": "New York-Newark-Jersey City, NY-NJ-PA",
      "drinking_places_7224": 4200,
      "food_and_drinking_722": 62000,
      "population": 19800000,
      "bars_per_10k": 2.12,
      "food_drink_per_10k": 31.3
    },
    "new-orleans-la": {
      "msa_fips": "35380",
      "msa_name": "New Orleans-Metairie, LA",
      "drinking_places_7224": 580,
      "food_and_drinking_722": 4100,
      "population": 1270000,
      "bars_per_10k": 4.57,
      "food_drink_per_10k": 32.3
    }
  }
}
```

## Validation
- All 92 markets should have data (some small ones may have suppressed bar counts)
- `bars_per_10k` should range from ~0.5 (low) to ~8+ (bar-heavy cities)
- Spot check: New Orleans, Key West, and Las Vegas should be HIGH. Suburban/sprawl cities like Mesa AZ, Arlington TX should be LOW.
- `food_drink_per_10k` should be between 15 and 50 for most metros
