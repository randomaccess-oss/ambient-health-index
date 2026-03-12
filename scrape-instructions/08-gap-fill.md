# Task 8: Gap Fill — Second Pass for 35 Missing Markets

## Goal
The first scrape pass missed 35 markets. This task fills ALL gaps in a single pass:
- **21 markets** need Walk Score + Transit Score
- **30 markets** need Census data (commuting, migration, CBP bar counts, density)
- 16 markets need BOTH (overlap)

Run this as one task. Output TWO files that get merged into the existing data files.

---

## PART A: Walk Score (21 markets)

### Instructions
Fetch `https://www.walkscore.com/score/{City}-{State}` for each city below. Extract Walk Score (0–100) and Transit Score (0–100, null if not shown). Wait 2–3 seconds between requests.

### Markets to scrape

```
hoboken-nj         → Hoboken-NJ
new-haven-ct       → New-Haven-CT
newark-nj          → Newark-NJ
albany-ny          → Albany-NY
duluth-mn          → Duluth-MN
anchorage-ak       → Anchorage-AK
reno-nv            → Reno-NV
norfolk-va         → Norfolk-VA
green-bay-wi       → Green-Bay-WI
la-crosse-wi       → La-Crosse-WI
mobile-al          → Mobile-AL
portsmouth-nh      → Portsmouth-NH
annapolis-md       → Annapolis-MD
santa-barbara-ca   → Santa-Barbara-CA
fort-lauderdale-fl → Fort-Lauderdale-FL
san-juan-pr        → San-Juan-PR  (may need "San-Juan-Puerto-Rico" — try variations)
baton-rouge-la     → Baton-Rouge-LA
grand-rapids-mi    → Grand-Rapids-MI
fort-collins-co    → Fort-Collins-CO
iowa-city-ia       → Iowa-City-IA
provo-ut           → Provo-UT
```

### Output format
Save as `walkscore-gap-fill.json`:
```json
{
  "source": "Walk Score (walkscore.com)",
  "fetched_date": "2026-03-XX",
  "markets": {
    "hoboken-nj": { "walk_score": 96, "transit_score": 82 },
    "new-haven-ct": { "walk_score": 72, "transit_score": 55 }
  }
}
```

---

## PART B: Census Data (30 markets)

### What to pull
For each market below, you need 4 values from Census APIs:

1. **Commuting** (ACS Table S0801): commute_rate + mean_commute_minutes
2. **Migration** (ACS Table S0701): migration_rate
3. **Bar counts** (CBP, NAICS 7224): drinking_places + bars_per_10k
4. **Density** (ACS population + Gazetteer land area): msa_density + urban_density

### MSA FIPS codes for each market

**CRITICAL**: Here are the exact MSA FIPS codes. The first pass failed because the AI had to look these up and missed them. Use these directly.

```
milwaukee-wi        → 33340  (Milwaukee-Waukesha, WI)
baltimore-md        → 12580  (Baltimore-Columbia-Towson, MD)
san-jose-ca         → 41940  (San Jose-Sunnyvale-Santa Clara, CA)
jacksonville-fl     → 27260  (Jacksonville, FL)
providence-ri       → 39300  (Providence-Warwick, RI-MA)
charleston-sc       → 16700  (Charleston-North Charleston, SC)
burlington-vt       → 15540  (Burlington-South Burlington, VT)
bend-or             → 13460  (Bend, OR — Micropolitan)
honolulu-hi         → 46520  (Urban Honolulu, HI)
portland-me         → 38860  (Portland-South Portland, ME)
santa-fe-nm         → 42140  (Santa Fe, NM)
chattanooga-tn      → 16860  (Chattanooga, TN-GA)
fort-worth-tx       → 19100  (Dallas-Fort Worth-Arlington, TX — SAME MSA as Dallas, use DFW data)
norfolk-va          → 47260  (Virginia Beach-Norfolk-Newport News, VA-NC)
reno-nv             → 39900  (Reno, NV)
albany-ny           → 10580  (Albany-Schenectady-Troy, NY)
new-haven-ct        → 35300  (New Haven-Milford, CT)
newark-nj           → 35084  (Newark, NJ-PA — Metropolitan Division of NYC MSA)
green-bay-wi        → 24580  (Green Bay, WI)
la-crosse-wi        → 29100  (La Crosse-Onalaska, WI-MN)
mobile-al           → 33660  (Mobile, AL)
portsmouth-nh       → 40484  (Portsmouth, NH — part of Dover-Durham-Portsmouth, NH micro)
annapolis-md        → 12580  (Part of Baltimore MSA — use Baltimore data, OR Anne Arundel County FIPS 24003)
santa-barbara-ca    → 42200  (Santa Maria-Santa Barbara, CA)
fort-lauderdale-fl  → 33100  (Miami-Fort Lauderdale-Pompano Beach, FL — SAME MSA as Miami, use Miami data)
duluth-mn           → 20260  (Duluth, MN-WI)
anchorage-ak        → 11260  (Anchorage, AK)
san-juan-pr         → 41980  (San Juan-Bayamón-Caguas, PR)
iowa-city-ia        → 26980  (Iowa City, IA)
provo-ut            → 39340  (Provo-Orem, UT)
```

### Special cases — READ CAREFULLY

1. **fort-worth-tx** shares the DFW MSA (19100) with Dallas. Use the same data as dallas-tx.
2. **fort-lauderdale-fl** shares the Miami MSA (33100) with Miami. Use the same data as miami-fl.
3. **annapolis-md** is part of the Baltimore MSA (12580). Either use Baltimore MSA data or query Anne Arundel County (FIPS 24003) specifically.
4. **newark-nj** is a Metropolitan Division (35084) within the NYC MSA. Try querying as a metro division first. If that fails, use NYC MSA data.
5. **hoboken-nj** is within the NYC MSA but too small for its own metro data. Use NYC MSA data (35620) — same as new-york-ny.
6. **san-juan-pr** — Puerto Rico uses different Census geography. The API call is:
   ```
   https://api.census.gov/data/2022/acs/acs5/subject?get=NAME,S0801_C01_001E,S0801_C01_046E,S0801_C01_003E&for=metropolitan%20statistical%20area/micropolitan%20statistical%20area:41980
   ```
   If this doesn't work, try county-level for San Juan Municipio (FIPS: 72127).
7. **portsmouth-nh** — Small metro. If MSA-level data isn't available, use Rockingham County, NH (FIPS 33015).

### API calls

**Commuting (all MSAs at once):**
```
https://api.census.gov/data/2022/acs/acs5/subject?get=NAME,S0801_C01_001E,S0801_C01_046E,S0801_C01_003E&for=metropolitan%20statistical%20area/micropolitan%20statistical%20area:*
```
Filter to the FIPS codes listed above.

**Migration (all MSAs at once):**
```
https://api.census.gov/data/2022/acs/acs5/subject?get=NAME,S0701_C01_001E,S0701_C03_001E,S0701_C04_001E&for=metropolitan%20statistical%20area/micropolitan%20statistical%20area:*
```

**CBP bar counts (all counties, NAICS 7224):**
```
https://api.census.gov/data/2022/cbp?get=NAME,ESTAB,NAICS2017&for=county:*&NAICS2017=7224
```
Then aggregate counties → MSAs using the delineation file.

**Population + density:**
```
https://api.census.gov/data/2022/acs/acs5?get=NAME,B01001_001E&for=metropolitan%20statistical%20area/micropolitan%20statistical%20area:*
```
Plus the Gazetteer file for land area:
`https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2023_Gazetteer/2023_Gaz_cbsa_national.txt`

### Calculations
For each market:
- `commute_rate` = 1 - (S0801_C01_046E / S0801_C01_001E)
- `mean_commute_minutes` = S0801_C01_003E
- `migration_rate` = (S0701_C03_001E + S0701_C04_001E) / S0701_C01_001E
- `bars_per_10k` = (ESTAB count for NAICS 7224 in MSA) / population * 10000
- `msa_density_per_sqmi` = population / land_area_sqmi
- `urban_density_per_sqmi` = from urbanized area data if available, else null

### Output format
Save as `census-gap-fill.json`:
```json
{
  "source": "U.S. Census Bureau, ACS 2022 + CBP 2022 + Gazetteer",
  "fetched_date": "2026-03-XX",
  "markets": {
    "milwaukee-wi": {
      "msa_fips": "33340",
      "msa_name": "Milwaukee-Waukesha, WI",
      "commute_rate": 0.862,
      "mean_commute_minutes": 22.4,
      "migration_rate": 0.041,
      "drinking_places_7224": 890,
      "population": 1574000,
      "bars_per_10k": 5.65,
      "msa_land_area_sqmi": 1451,
      "msa_density_per_sqmi": 1084.8,
      "urban_density_per_sqmi": 2876
    },
    "hoboken-nj": {
      "msa_fips": "35620",
      "msa_name": "New York-Newark-Jersey City, NY-NJ-PA (shared MSA)",
      "commute_rate": 0.854,
      "mean_commute_minutes": 37.1,
      "migration_rate": 0.029,
      "drinking_places_7224": 4187,
      "population": 19908595,
      "bars_per_10k": 2.1,
      "msa_land_area_sqmi": 6718,
      "msa_density_per_sqmi": 2963.5,
      "urban_density_per_sqmi": 5319,
      "note": "Uses NYC MSA data — Hoboken is within the NYC metropolitan area"
    }
  }
}
```

---

## AFTER SCRAPING: How to merge

Once you have both files (`walkscore-gap-fill.json` and `census-gap-fill.json`), merge them into the existing data files:

```python
import json

# Merge Walk Score
ws = json.load(open('walkscore-data.json'))
gap_ws = json.load(open('walkscore-gap-fill.json'))
ws['markets'].update(gap_ws['markets'])
json.dump(ws, open('walkscore-data.json', 'w'), indent=2)

# Merge Census — add to all 4 files
gap_census = json.load(open('census-gap-fill.json'))
for filename in ['census-commuting-data.json', 'census-migration-data.json',
                  'census-cbp-data.json', 'census-density-data.json']:
    existing = json.load(open(filename))
    for mid, data in gap_census['markets'].items():
        if mid not in existing['markets']:
            # Map fields based on which file
            if 'commuting' in filename:
                existing['markets'][mid] = {
                    'msa_fips': data['msa_fips'], 'msa_name': data['msa_name'],
                    'commute_rate': data['commute_rate'],
                    'mean_commute_minutes': data['mean_commute_minutes']
                }
            elif 'migration' in filename:
                existing['markets'][mid] = {
                    'msa_fips': data['msa_fips'], 'msa_name': data['msa_name'],
                    'migration_rate': data['migration_rate']
                }
            elif 'cbp' in filename:
                existing['markets'][mid] = {
                    'msa_fips': data['msa_fips'], 'msa_name': data['msa_name'],
                    'drinking_places_7224': data['drinking_places_7224'],
                    'population': data['population'],
                    'bars_per_10k': data['bars_per_10k']
                }
            elif 'density' in filename:
                existing['markets'][mid] = {
                    'msa_fips': data['msa_fips'], 'msa_name': data['msa_name'],
                    'population': data['population'],
                    'msa_land_area_sqmi': data['msa_land_area_sqmi'],
                    'msa_density_per_sqmi': data['msa_density_per_sqmi'],
                    'urban_density_per_sqmi': data.get('urban_density_per_sqmi')
                }
    json.dump(existing, open(filename, 'w'), indent=2)

print('Merged. Now re-run: python3 scripts/assemble.py')
```

Then re-run the assembly: `python3 scripts/assemble.py`

## Validation
After merge + re-assembly:
- All 92 markets should show `dataQuality: "full"` (or at worst `"partial"` for PR)
- 0 markets should be `"estimated"`
- Missing data warnings should drop from 35 to 0 (or 1 for San Juan if PR data is unavailable)
