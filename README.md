# WA Traffic Data Analysis

A pure-Python tool that reads a CSV of Western Australian traffic-count data and produces three analyses for a chosen Administrative Region: yearly summaries, sites ranked within each Local Government Area, and a cosine-similarity comparison of weekday versus weekend heavy-vehicle traffic.

Built for CITS1401 (Computational Thinking with Python) at the University of Western Australia. The constraint for the project was to use the Python standard library only, with no external packages, so all parsing, statistics, and similarity maths are implemented from scratch.

## What it does

The program takes a CSV file and a region name, validates and filters the data, then returns three outputs.

**Output 1: Yearly summary.** For each traffic year in the region, it reports the number of sites, the mean daily traffic (MON_SUN), the sample standard deviation, and the site carrying the highest percentage of heavy vehicles. Ties on heavy-vehicle percentage are broken by the alphabetically earliest GlobalID.

**Output 2: Sites ranked by Local Government Area.** Within each LGA that has at least three sites, every site is ranked by daily traffic volume in descending order, with ties again broken by GlobalID.

**Output 3: Weekday vs weekend comparison.** For each year, it averages the weekday (MON_FRI) and weekend (SAT_SUN) heavy-vehicle percentages, then computes the cosine similarity between the two year-by-year vectors to measure how closely the two patterns track each other.

## Data validation

Before any analysis runs, every row is checked and unclean data is discarded:

- Coordinate and ID fields (X, Y, LG_NO, RA_NO, OBJECTID) must parse as floats.
- Traffic-count and percentage fields must parse as non-negative floats.
- Text fields (site, road name, year, region, and so on) must be present and non-empty.
- Any SITE_NO that appears more than once is treated as a duplicate, and every row sharing that ID is removed.

Only rows belonging to the requested region survive into the analysis.

## How to run

The program is structured as a `main` function rather than a script, which is how it was graded. Call it from a Python file or an interactive session:

```python
from traffic_analysis import main

op1, op2, op3 = main("traffic_data.csv", "Metropolitan")

print(op1)  # yearly summary
print(op2)  # sites ranked by LGA
print(op3)  # weekday vs weekend cosine similarity
```

`main` returns a tuple of `(dict, dict, list)`. If the file is missing, empty, or the inputs are invalid, it safely returns empty structures `({}, {}, [])` rather than raising.

## Expected CSV format

The input is expected to contain (at minimum) the following columns. Header matching is case-insensitive.

| Column | Meaning |
| --- | --- |
| SITE_NO | Unique site identifier |
| ROAD_NAME, LOCATION_DESC | Site location |
| TRAFFIC_YEAR | Year of the count |
| LG_NAME, RA_NAME | Local Government Area and Administrative Region |
| MON_SUN, MON_FRI, SAT_SUN | Average daily traffic counts |
| PCT_HEAVY_MON_SUN, PCT_HEAVY_MON_FRI, PCT_HEAVY_SAT_SUN | Heavy-vehicle percentages |
| X, Y, LG_NO, RA_NO, OBJECTID, GLOBALID | Coordinates and identifiers |

## What this project demonstrates

- CSV parsing and data cleaning without external libraries
- Statistics implemented by hand: mean, sample standard deviation, and cosine similarity
- Grouping and aggregating records by year and by region
- Deterministic tie-breaking and sorting with composite sort keys
- Defensive input handling that fails gracefully

## Requirements

Python 3. No third-party dependencies.
