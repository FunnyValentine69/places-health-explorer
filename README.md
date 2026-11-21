# Community Health Explorer

A Streamlit dashboard for exploring CDC PLACES county health estimates. Pick a state and
a health measure to see county rankings, the spread across counties, and a county map. A
second section compares health-related social needs (food insecurity, housing insecurity,
transportation barriers, and others) with health outcomes, to look at health equity.

Final project for BMI 540, Oregon Health & Science University, Fall 2026.

## Data

- Source: [CDC PLACES: Local Data for Better Health, County Data, 2025 release](https://data.cdc.gov/d/swc5-untb)
  (data.cdc.gov, dataset id swc5-untb). Public, aggregate county estimates modeled from the
  BRFSS survey. No individual patient records.
- The app uses age-adjusted prevalence, which CDC recommends for comparing counties
  ([PLACES: Using the Data](https://www.cdc.gov/places/faqs/using-data/index.html)).
- Known gaps, shown in the app: Kentucky and Pennsylvania counties have no 2023 estimates
  (only five 2022 measures), and social needs measures cover 39 states and DC.

## Files

- `prepare_data.py`: imports, explores, and cleans the raw CDC file and writes the cleaned file
- `data/places_county_clean.csv`: cleaned data the app reads (one row per county and measure)
- `app.py`: the Streamlit app
- `requirements.txt`: the packages the app needs

The raw CDC file (53 MB) is not in the repository. `prepare_data.py` downloads it into
`data/` if it is missing.

## Run it locally

Create and activate a virtual environment, then:

```
pip install -r requirements.txt
python prepare_data.py
streamlit run app.py
```
