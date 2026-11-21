import os

import pandas as pd

RAW_FILE = "data/PLACES_County_2025.csv"
CLEAN_FILE = "data/places_county_clean.csv"
RAW_URL = "https://data.cdc.gov/api/views/swc5-untb/rows.csv?accessType=DOWNLOAD"

#Download raw CDC file if missing
if not os.path.exists(RAW_FILE):
    print("Downloading raw data from data.cdc.gov...")
    pd.read_csv(RAW_URL, dtype={"LocationID": str}, low_memory=False).to_csv(RAW_FILE, index=False)

#Load raw data, FIPS codes as text
raw = pd.read_csv(RAW_FILE, dtype={"LocationID": str}, low_memory=False)
print("Raw shape:", raw.shape)

#Explore raw file
print("\nMissing values per column:")
print(raw.isna().sum()[raw.isna().sum() > 0])
print("\nYears:", raw["Year"].value_counts().to_dict())
print("Value types:", raw["Data_Value_Type"].value_counts().to_dict())
print("Measures per category:")
print(raw.groupby("Category")["MeasureId"].nunique())
print("\nFootnotes:", raw["Data_Value_Footnote"].value_counts().to_dict())

#States with no 2023 measures
counties = raw[raw["StateAbbr"] != "US"]
states_2023 = counties[counties["Year"] == 2023]["StateAbbr"].unique()
print("\nStates missing all 2023 measures:", sorted(set(counties["StateAbbr"]) - set(states_2023)))

#States with no social needs measures
social = counties[counties["Category"] == "Health-Related Social Needs"]
print("States and DC with social needs measures:", social["StateAbbr"].nunique(), "of", counties["StateAbbr"].nunique())
print("Missing social needs:", sorted(set(counties["StateAbbr"]) - set(social["StateAbbr"])))

#County rows only, drop US summary row
clean = counties.copy()

#Age-adjusted prevalence (CDC recommended for county comparisons)
clean = clean[clean["DataValueTypeID"] == "AgeAdjPrv"]

#Drop suppressed values (Loving County, TX, pop < 50)
clean = clean.dropna(subset=["Data_Value"])

#Split "POINT (lon lat)" into longitude and latitude
coords = clean["Geolocation"].str.extract(r"POINT \((\S+) (\S+)\)").astype(float)
clean = clean.assign(lon=coords[0].round(4), lat=coords[1].round(4))

#Keep app columns, short names
clean = clean[["StateAbbr", "StateDesc", "LocationName", "LocationID", "Category",
               "MeasureId", "Short_Question_Text", "Measure", "Year", "Data_Value",
               "Low_Confidence_Limit", "High_Confidence_Limit", "TotalPop18plus", "lat", "lon"]]
clean.columns = ["state", "state_name", "county", "fips", "category", "measure_id", "measure",
                 "description", "year", "value", "low_ci", "high_ci", "adult_pop", "lat", "lon"]

#Rename insurance measure: higher = more uninsured
clean["measure"] = clean["measure"].replace("Health Insurance", "Lack of Health Insurance")

#Label independent cities sharing a county name (FIPS 510+)
names = clean[["state", "county", "fips"]].drop_duplicates()
shared = names[names.duplicated(["state", "county"], keep=False)]
print("\nShared county and city names:", len(shared))
is_city = clean["fips"].isin(shared["fips"]) & (clean["fips"].str[2:] >= "510")
clean.loc[is_city, "county"] = clean.loc[is_city, "county"] + " city"

#Check cleaned data before saving
print("\nClean shape:", clean.shape)
print("Counties:", clean["fips"].nunique(), "States:", clean["state"].nunique(),
      "Measures:", clean["measure_id"].nunique())
print("Missing values left:", int(clean.isna().sum().sum()))
print("Duplicate county names left:", int(clean.duplicated(["state", "county", "measure_id"]).sum()))

#Quick analysis: highest adult obesity counties
obesity = clean[clean["measure_id"] == "OBESITY"].sort_values("value", ascending=False)
print("\nTop 5 counties, adult obesity (age-adjusted %):")
print(obesity[["state", "county", "value"]].head().to_string(index=False))

#Save cleaned file for app
clean.to_csv(CLEAN_FILE, index=False)
print("\nSaved", CLEAN_FILE, round(os.path.getsize(CLEAN_FILE) / 1e6, 1), "MB")
