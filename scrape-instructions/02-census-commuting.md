# Task 2: Census ACS Commuting Data

## What You're Getting
Two numbers per metro area from the U.S. Census American Community Survey (ACS):
- **Commute-to-work rate**: % of workers who commute (i.e., do NOT work from home)
- **Mean travel time to work**: Average commute in minutes

These feed into: **Temporal Synchronization**
Logic: Higher commute rate + shorter commute time = people arrive at places at the same time = higher temporal sync score.

## Data Source
**American Community Survey 5-Year Estimates, Table S0801 (Commuting Characteristics by Sex)**
- API endpoint: `https://api.census.gov/data/2022/acs/acs5/subject`
- No API key required for small queries (but recommended for bulk — get one free at https://api.census.gov/data/key_signup.html)
- Geographic level: Metropolitan Statistical Area (MSA)

## Exact Steps

### Step 1: Understand the variables
From table S0801:
- `S0801_C01_001E` = Total workers 16 years and over (denominator)
- `S0801_C01_046E` = Workers who worked from home (count)
- `S0801_C01_046E / S0801_C01_001E` = WFH rate → subtract from 1 to get commute rate
- `S0801_C01_046E` might also be available as a percentage directly. Check both.
- `S0801_C01_003E` = Mean travel time to work (minutes)

Alternative approach using table B08301 (Means of Transportation to Work):
- `B08301_001E` = Total workers
- `B08301_021E` = Worked from home
- Commute rate = 1 - (B08301_021E / B08301_001E)

And table B08303 (Travel Time to Work):
- Use `B08135_001E` = Aggregate travel time / `B08301_001E` - `B08301_021E` = mean commute time
- OR use the pre-calculated mean from S0801.

### Step 2: Find MSA FIPS codes for each market
Each of the 92 markets corresponds to a Metropolitan Statistical Area (MSA) or Metropolitan Division. You need the MSA FIPS code for each.

Key MSA FIPS codes (look up the rest on Census Bureau's delineation files at https://www.census.gov/geographies/reference-files/time-series/demo/metro-micro/delineation-files.html):

```
New York-Newark-Jersey City, NY-NJ-PA MSA: 35620
Los Angeles-Long Beach-Anaheim, CA MSA: 31080
Chicago-Naperville-Elgin, IL-IN-WI MSA: 16980
Houston-The Woodlands-Sugar Land, TX MSA: 26420
Phoenix-Mesa-Chandler, AZ MSA: 38060
Philadelphia-Camden-Wilmington, PA-NJ-DE-MD MSA: 37980
San Antonio-New Braunfels, TX MSA: 41700
San Diego-Chula Vista-Carlsbad, CA MSA: 41740
Dallas-Fort Worth-Arlington, TX MSA: 19100
Miami-Fort Lauderdale-Pompano Beach, FL MSA: 33100
Atlanta-Sandy Springs-Alpharetta, GA MSA: 12060
Boston-Cambridge-Newton, MA-NH MSA: 14460
San Francisco-Oakland-Berkeley, CA MSA: 41860
Seattle-Tacoma-Bellevue, WA MSA: 42660
Denver-Aurora-Lakewood, CO MSA: 19740
Washington-Arlington-Alexandria, DC-VA-MD-WV MSA: 47900
Nashville-Davidson--Murfreesboro--Franklin, TN MSA: 34980
Austin-Round Rock-Georgetown, TX MSA: 12420
Portland-Vancouver-Hillsboro, OR-WA MSA: 38900
Las Vegas-Henderson-Paradise, NV MSA: 29820
Detroit-Warren-Dearborn, MI MSA: 19820
Minneapolis-St. Paul-Bloomington, MN-WI MSA: 33460
```

For the remaining 70 markets, look up the MSA FIPS code on the Census delineation file. Some small markets (Marfa TX, Door County WI, Telluride CO, etc.) may be in Micropolitan Statistical Areas or not in any MSA. For those:
- Try the county-level query instead (use county FIPS code with `for=county:*&in=state:XX`)
- If no MSA exists, query at the county level

### Step 3: Query the API
Example API call for one MSA:
```
https://api.census.gov/data/2022/acs/acs5/subject?get=NAME,S0801_C01_001E,S0801_C01_046E,S0801_C01_003E&for=metropolitan%20statistical%20area/micropolitan%20statistical%20area:35620
```

For bulk (all MSAs at once):
```
https://api.census.gov/data/2022/acs/acs5/subject?get=NAME,S0801_C01_001E,S0801_C01_046E,S0801_C01_003E&for=metropolitan%20statistical%20area/micropolitan%20statistical%20area:*
```

This returns ALL MSAs in one call. Then filter to the 92 you need.

### Step 4: Calculate values
For each market:
- `commute_rate` = 1 - (S0801_C01_046E / S0801_C01_001E) → decimal, e.g., 0.87 means 87% commute
- `mean_commute_minutes` = S0801_C01_003E → number, e.g., 34.5

### Step 5: Handle edge cases
- Some very small towns (Marfa, Telluride, Eureka Springs) may not have MSA-level data. Use county-level data instead.
- If a variable returns null or -666666666 (Census null marker), note it and skip that market for manual research later.
- DC is its own MSA (47900) — Washington-Arlington-Alexandria.

## Output Format
Save as `census-commuting-data.json`:
```json
{
  "source": "U.S. Census Bureau, ACS 5-Year Estimates 2022, Table S0801",
  "fetched_date": "2026-03-10",
  "url": "https://api.census.gov/data/2022/acs/acs5/subject",
  "markets": {
    "new-york-ny": {
      "msa_fips": "35620",
      "msa_name": "New York-Newark-Jersey City, NY-NJ-PA",
      "total_workers": 9500000,
      "work_from_home": 1200000,
      "commute_rate": 0.874,
      "mean_commute_minutes": 37.1
    },
    "boise-id": {
      "msa_fips": "14260",
      "msa_name": "Boise City, ID",
      "total_workers": 350000,
      "work_from_home": 52000,
      "commute_rate": 0.851,
      "mean_commute_minutes": 22.3
    }
  }
}
```

## Validation
- All 92 markets should have data (or explicit nulls for tiny markets)
- `commute_rate` should be between 0.5 and 1.0 (very few cities have >50% WFH)
- `mean_commute_minutes` should be between 10 and 45 for US cities
- Spot check: NYC should have long commutes (~37 min), smaller cities shorter (~20 min)
