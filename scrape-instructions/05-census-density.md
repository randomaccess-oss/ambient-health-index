# Task 5: Census Population Density

## What You're Getting
Per metro area:
- **Population density**: People per square mile at the MSA level

This feeds into: **Spatial Concentration**
Logic: Higher density = more people packed together = higher spatial concentration.

## Data Source
**Census Bureau, ACS 5-Year Estimates + Gazetteer Files (for land area)**
- Population: ACS API
- Land area: Census Gazetteer files OR calculated from MSA definitions

## Exact Steps

### Step 1: Get MSA populations
You may already have this from Task 4 (CBP). If so, reuse it. Otherwise:
```
https://api.census.gov/data/2022/acs/acs5?get=NAME,B01001_001E&for=metropolitan%20statistical%20area/micropolitan%20statistical%20area:*
```

### Step 2: Get MSA land area
Option A — Gazetteer file (RECOMMENDED):
Download the MSA Gazetteer file from:
`https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2023_Gazetteer/2023_Gaz_cbsa_national.txt`

This is a tab-delimited file with columns:
- `GEOID` = MSA FIPS code
- `NAME` = MSA name
- `ALAND_SQMI` = Land area in square miles

Option B — If the Gazetteer file URL has changed, search for "Census Gazetteer files CBSA" on census.gov. The file is updated annually.

### Step 3: Calculate density
For each market:
- `density` = population / ALAND_SQMI (people per square mile)

### Step 4: Important nuance — urbanized area vs. MSA
MSA density can be misleading because MSAs include large rural areas. For example, the Phoenix MSA includes vast empty desert, so its MSA density is low even though central Phoenix is dense.

If possible, ALSO get the **urbanized area density** from the Census:
- Table: Census Bureau Urban Areas (UA) data
- URL: `https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2020_Gazetteer/2020_Gaz_ua_national.txt`
- This gives density for just the built-up urban area, which is more meaningful.

Record BOTH if available:
- `msa_density` = population / MSA land area (broader)
- `urban_density` = urbanized area population / urbanized area land area (tighter, more useful)

### Step 5: Handle edge cases
- Small markets (Marfa TX, Telluride CO) may be in Micropolitan Statistical Areas or not in any CBSA. Use county-level data.
- Door County WI is a county, not a city — use the county's data directly.
- Some MSAs span huge areas (e.g., Riverside-San Bernardino CA). The MSA density will look low but the urban core is dense. Urbanized area density is more useful here.

## Output Format
Save as `census-density-data.json`:
```json
{
  "source": "U.S. Census Bureau, ACS 2022 + Gazetteer Files",
  "fetched_date": "2026-03-10",
  "url": "https://api.census.gov/data/2022/acs/acs5",
  "markets": {
    "new-york-ny": {
      "msa_fips": "35620",
      "msa_name": "New York-Newark-Jersey City, NY-NJ-PA",
      "population": 19800000,
      "msa_land_area_sqmi": 6720,
      "msa_density_per_sqmi": 2946,
      "urban_density_per_sqmi": 5319
    },
    "boise-id": {
      "msa_fips": "14260",
      "msa_name": "Boise City, ID",
      "population": 780000,
      "msa_land_area_sqmi": 3965,
      "msa_density_per_sqmi": 197,
      "urban_density_per_sqmi": 2410
    }
  }
}
```

## Validation
- All 92 markets should have `msa_density_per_sqmi`
- `msa_density_per_sqmi` should range from ~20 (rural micros) to ~3000+ (NYC metro)
- `urban_density_per_sqmi` should range from ~1000 to ~6000+
- Spot check: NYC and San Francisco should be highest. Sprawl cities (Phoenix, Jacksonville, San Antonio) should have LOW MSA density but moderate urban density.
- Key West, Honolulu should have high density (island constraints)
