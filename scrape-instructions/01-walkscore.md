# Task 1: Walk Score + Transit Score

## What You're Getting
Two numbers per city from walkscore.com:
- **Walk Score** (0–100): How walkable the city is
- **Transit Score** (0–100): How good public transit is

These feed into:
- Spatial Concentration (Walk Score)
- Planning Cost (Transit Score)

## Exact Steps

### Step 1: Understand the URL pattern
Walk Score pages live at: `https://www.walkscore.com/score/CITY_STATE`

Examples:
- https://www.walkscore.com/score/New-York-NY
- https://www.walkscore.com/score/Chicago-IL
- https://www.walkscore.com/score/Key-West-FL
- https://www.walkscore.com/score/Boise-ID

The pattern is: city name with spaces replaced by hyphens, followed by hyphen, followed by state abbreviation. All URL-safe characters.

### Step 2: Fetch each page
For each of the 92 markets below, fetch the Walk Score page. The page contains both the Walk Score and Transit Score displayed prominently.

Look for:
- The Walk Score number (large number, 0–100, with label "Walk Score")
- The Transit Score number (0–100, with label "Transit Score")
- Some cities may not have a Transit Score (smaller cities). Record `null` for those.

### Step 3: Handle edge cases
- If a city name has a special character or doesn't resolve, try variations:
  - "St. Louis" → try "St.-Louis-MO" or "Saint-Louis-MO"
  - "Winston-Salem" → try "Winston-Salem-NC" or "Winston--Salem-NC"
- If Walk Score returns a "city not found" page, try searching on walkscore.com directly and note the correct URL.
- Some small markets may only have Walk Score, not Transit Score. That's fine — record Transit Score as null.

### Step 4: Rate limiting
- Add 2–3 seconds between requests to avoid being blocked
- If you get a 429 or CAPTCHA, wait 60 seconds and retry
- Total runtime estimate: ~5–8 minutes for 92 cities

## Output Format
Save as `walkscore-data.json`:
```json
{
  "source": "Walk Score (walkscore.com)",
  "fetched_date": "2026-03-10",
  "url": "https://www.walkscore.com/score/{city}-{state}",
  "markets": {
    "new-york-ny": {
      "walk_score": 88,
      "transit_score": 89
    },
    "chicago-il": {
      "walk_score": 78,
      "transit_score": 65
    },
    "boise-id": {
      "walk_score": 39,
      "transit_score": null
    }
  }
}
```

## Full Market List (92 cities)
Use the `id` field as the key, and derive the URL from `city` and `state`:

```
new-york-ny → New-York-NY
los-angeles-ca → Los-Angeles-CA
chicago-il → Chicago-IL
houston-tx → Houston-TX
phoenix-az → Phoenix-AZ
philadelphia-pa → Philadelphia-PA
san-antonio-tx → San-Antonio-TX
san-diego-ca → San-Diego-CA
dallas-tx → Dallas-TX
miami-fl → Miami-FL
atlanta-ga → Atlanta-GA
boston-ma → Boston-MA
san-francisco-ca → San-Francisco-CA
seattle-wa → Seattle-WA
denver-co → Denver-CO
washington-dc → Washington-DC
nashville-tn → Nashville-TN
austin-tx → Austin-TX
portland-or → Portland-OR
las-vegas-nv → Las-Vegas-NV
detroit-mi → Detroit-MI
minneapolis-mn → Minneapolis-MN
tampa-fl → Tampa-FL
charlotte-nc → Charlotte-NC
orlando-fl → Orlando-FL
st-louis-mo → St.-Louis-MO (or Saint-Louis-MO — try both)
pittsburgh-pa → Pittsburgh-PA
baltimore-md → Baltimore-MD
indianapolis-in → Indianapolis-IN
columbus-oh → Columbus-OH
san-jose-ca → San-Jose-CA
jacksonville-fl → Jacksonville-FL
fort-worth-tx → Fort-Worth-TX
memphis-tn → Memphis-TN
louisville-ky → Louisville-KY
richmond-va → Richmond-VA
new-orleans-la → New-Orleans-LA
salt-lake-city-ut → Salt-Lake-City-UT
hartford-ct → Hartford-CT
buffalo-ny → Buffalo-NY
milwaukee-wi → Milwaukee-WI
kansas-city-mo → Kansas-City-MO
oklahoma-city-ok → Oklahoma-City-OK
raleigh-nc → Raleigh-NC
cleveland-oh → Cleveland-OH
cincinnati-oh → Cincinnati-OH
sacramento-ca → Sacramento-CA
virginia-beach-va → Virginia-Beach-VA
omaha-ne → Omaha-NE
colorado-springs-co → Colorado-Springs-CO
tucson-az → Tucson-AZ
mesa-az → Mesa-AZ
tulsa-ok → Tulsa-OK
arlington-tx → Arlington-TX
albuquerque-nm → Albuquerque-NM
el-paso-tx → El-Paso-TX
honolulu-hi → Honolulu-HI
savannah-ga → Savannah-GA
charleston-sc → Charleston-SC
madison-wi → Madison-WI
asheville-nc → Asheville-NC
boise-id → Boise-ID
des-moines-ia → Des-Moines-IA
spokane-wa → Spokane-WA
knoxville-tn → Knoxville-TN
greenville-sc → Greenville-SC
chattanooga-tn → Chattanooga-TN
lexington-ky → Lexington-KY
birmingham-al → Birmingham-AL
rochester-ny → Rochester-NY
providence-ri → Providence-RI
santa-fe-nm → Santa-Fe-NM
key-west-fl → Key-West-FL
boulder-co → Boulder-CO
ann-arbor-mi → Ann-Arbor-MI
burlington-vt → Burlington-VT
portland-me → Portland-ME
ithaca-ny → Ithaca-NY
missoula-mt → Missoula-MT
bend-or → Bend-OR
flagstaff-az → Flagstaff-AZ
traverse-city-mi → Traverse-City-MI
fredericksburg-va → Fredericksburg-VA
oxford-ms → Oxford-MS
athens-ga → Athens-GA
galveston-tx → Galveston-TX
marfa-tx → Marfa-TX
sedona-az → Sedona-AZ
eureka-springs-ar → Eureka-Springs-AR
door-county-wi → Door-County-WI (NOTE: this is a county, not a city — try "Sturgeon-Bay-WI" as the main town)
telluride-co → Telluride-CO
park-city-ut → Park-City-UT
```

## Validation
After scraping, verify:
- All 92 markets have a `walk_score` value (number 0–100)
- Transit scores are present for most large/mega cities, null is OK for small towns
- No duplicates, no missing markets
