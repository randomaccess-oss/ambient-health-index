# Task 6: NIAAA Per-Capita Alcohol Consumption

## What You're Getting
Per STATE (not city — this is state-level data, mapped to markets):
- **Per-capita ethanol consumption** in gallons per year
- Broken out by beverage type: beer, wine, spirits

This feeds into: **Social Permission**
Logic: Higher per-capita consumption = drinking is more culturally normalized = higher social permission score.

## Data Source
**NIAAA (National Institute on Alcohol Abuse and Alcoholism) Surveillance Report #120**
- Title: "Apparent Per Capita Alcohol Consumption: National, State, and Regional Trends, 1977–2021"
- URL: https://pubs.niaaa.nih.gov/publications/surveillance120/tab1_2021.htm (Table 1 — total per capita)
- Also check: https://pubs.niaaa.nih.gov/publications/surveillance-covid-19/CONS-US-covid.htm (more recent COVID-era data)

Alternative if the above URLs have changed:
- Search "NIAAA apparent per capita alcohol consumption state" on Google
- The data is in a well-known surveillance report series, published regularly
- You want the most recent year available

## Exact Steps

### Step 1: Navigate to the NIAAA data page
Go to the URL above. The table shows per-capita ethanol consumption (in gallons) by state for each year. Get the most recent year available (likely 2021 or 2022).

### Step 2: Extract the data
The table has columns for:
- State name
- Total ethanol consumption (gallons per capita, drinking-age population 14+)
- Beer
- Wine
- Spirits

You only NEED the **total** column, but grab all four for richer data.

### Step 3: Map states to markets
This is state-level data, so multiple markets in the same state get the same value:
- "new-york-ny", "buffalo-ny", "rochester-ny", "ithaca-ny" → all get New York state's value
- "austin-tx", "houston-tx", "dallas-tx", etc. → all get Texas's value
- DC has its own row (and typically shows VERY high consumption due to commuter/tourist effects)

States needed (derived from the 92 markets):
```
AL, AR, AZ, CA, CO, CT, DC, FL, GA, HI, IA, ID, IL, IN, KY, LA, MA, MD, ME, MI, MN, MO, MS, MT, NC, NE, NJ, NM, NV, NY, OH, OK, OR, PA, RI, SC, TN, TX, UT, VA, VT, WA, WI, WY
```
That's 44 states + DC = 45 values needed.

### Step 4: Record the data
For each state, record:
- `total_ethanol_gallons` (per capita, age 14+)
- `beer_gallons`
- `wine_gallons`
- `spirits_gallons`
- `data_year` (the year the data is from)

## Output Format
Save as `niaaa-consumption-data.json`:
```json
{
  "source": "NIAAA Surveillance Report, Apparent Per Capita Alcohol Consumption",
  "fetched_date": "2026-03-10",
  "url": "https://pubs.niaaa.nih.gov/publications/surveillance120/tab1_2021.htm",
  "data_year": 2021,
  "note": "Gallons of ethanol per capita (population age 14+). State-level data mapped to metro markets.",
  "states": {
    "NY": {
      "total_ethanol_gallons": 2.76,
      "beer_gallons": 1.08,
      "wine_gallons": 0.72,
      "spirits_gallons": 0.96
    },
    "TX": {
      "total_ethanol_gallons": 2.42,
      "beer_gallons": 1.21,
      "wine_gallons": 0.38,
      "spirits_gallons": 0.83
    },
    "UT": {
      "total_ethanol_gallons": 1.35,
      "beer_gallons": 0.62,
      "wine_gallons": 0.24,
      "spirits_gallons": 0.49
    },
    "DC": {
      "total_ethanol_gallons": 5.10,
      "beer_gallons": 1.30,
      "wine_gallons": 1.80,
      "spirits_gallons": 2.00
    }
  },
  "market_mapping": {
    "new-york-ny": "NY",
    "buffalo-ny": "NY",
    "austin-tx": "TX",
    "salt-lake-city-ut": "UT",
    "washington-dc": "DC"
  }
}
```

Include the FULL `market_mapping` object that maps all 92 market IDs to their state abbreviation.

## Validation
- All 45 states/DC should have data
- `total_ethanol_gallons` should range from ~1.3 (Utah, lowest) to ~5+ (DC, New Hampshire — border effect, Nevada)
- National average is approximately 2.5 gallons
- Spot check:
  - Utah should be LOWEST (strict alcohol laws, LDS population)
  - DC should be HIGHEST (inflated by commuters/tourists buying there)
  - New Hampshire should be very high (border sales effect — NH has no sales tax, people buy there from MA/VT)
  - Nevada should be high (tourism, Las Vegas)
  - Wisconsin should be above average (strong drinking culture)
  - Southern Baptist belt states (MS, AL, AR) should be below average

## Notes
- DC's number is artificially inflated because the denominator (DC residents) is small but consumption includes commuters and tourists. You might want to flag this. For scoring purposes, it still reflects high social permission in DC — bars are everywhere and drinking is normal.
- New Hampshire is inflated by border sales (no sales tax attracts MA/VT buyers). Flag this too.
- This is STATE-level data, so it can't distinguish between e.g. Austin vs. rural Texas. That's a known limitation. The CBP bar density data (Task 4) provides the city-level nuance.
