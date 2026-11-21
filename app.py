import altair as alt
import pandas as pd
import streamlit as st

st.title("Community Health Explorer")
st.write("Explore CDC PLACES health estimates for U.S. counties. Pick a state and a health measure "
         "to compare counties, then see how social needs relate to health outcomes.")


#Load the cleaned county data once and reuse it on every rerun
@st.cache_data
def load_data():
    return pd.read_csv("data/places_county_clean.csv", dtype={"fips": str})


places = load_data()

#Let the user pick a state, a category, and a measure
states = sorted(places["state_name"].unique())
state = st.selectbox("State", states, index=states.index("Oregon"))
col1, col2 = st.columns(2)
category = col1.selectbox("Category", sorted(places["category"].unique()), index=1)
measures = sorted(places[places["category"] == category]["measure"].unique())
measure = col2.selectbox("Measure", measures, index=measures.index("Obesity") if "Obesity" in measures else 0)

#Keep the chosen measure for the whole country and for the chosen state
national = places[places["measure"] == measure]
selected = national[national["state_name"] == state]
state_counties = places[places["state_name"] == state]["fips"].nunique()
us_median = national["value"].median()

#Warn when some counties in the state have no estimate for this measure
if len(selected) < state_counties:
    if state in ["Kentucky", "Pennsylvania"]:
        reason = "PLACES 2025 has no 2023 estimates for Kentucky and Pennsylvania counties."
    elif category == "Health-Related Social Needs":
        reason = "Social needs questions were asked in only 39 states and DC."
    else:
        reason = "Some estimates were suppressed for very small populations."
    st.warning(f"{len(selected)} of {state_counties} counties in {state} have data for this measure. {reason}")

if len(selected) > 0:
    col1, col2, col3 = st.columns(3)
    col1.metric("Counties with data", len(selected))
    col2.metric(f"{state} county median", f"{selected['value'].median():.1f}%")
    col3.metric("U.S. county median", f"{us_median:.1f}%")
    st.caption(f"Age-adjusted prevalence among adults, survey year {selected['year'].iloc[0]}.")

    st.subheader(f"Counties ranked by {measure.lower()}")
    col1, col2 = st.columns(2)
    col1.write("Highest 10")
    col1.bar_chart(selected.nlargest(10, "value"), x="county", y="value", y_label="%",
                   x_label="", horizontal=True, sort="-value")
    col2.write("Lowest 10")
    col2.bar_chart(selected.nsmallest(10, "value"), x="county", y="value", y_label="%",
                   x_label="", horizontal=True, sort="value")
    st.caption("Counties whose confidence intervals overlap (see the data table below) may not truly differ.")

    st.subheader(f"Distribution across {state} counties")
    histogram = (
        alt.Chart(selected)
        .mark_bar()
        .encode(
            alt.X("value:Q", bin=alt.Bin(maxbins=20), title=f"{measure} (%)"),
            alt.Y("count()", title="Number of counties")
        )
    )
    st.altair_chart(histogram, width="stretch")

    st.subheader("County map")
    #Color counties above the U.S. county median orange and the rest blue
    map_data = selected.assign(color=selected["value"].gt(us_median).map({True: "#f28e2b", False: "#4e79a7"}))
    st.map(map_data, latitude="lat", longitude="lon", color="color", size=4000)
    st.caption(f"Orange: above the U.S. county median ({us_median:.1f}%). Blue: at or below it.")

st.subheader("Social needs and health outcomes")
st.write("Health equity: do counties with more food insecurity, housing insecurity, or "
         "transportation barriers also have more chronic disease?")
col1, col2 = st.columns(2)
needs = sorted(places[places["category"] == "Health-Related Social Needs"]["measure"].unique())
need = col1.selectbox("Social need", needs, index=needs.index("Food Insecurity"))
outcomes = sorted(places[places["category"].isin(["Health Outcomes", "Health Status"])]["measure"].unique())
outcome = col2.selectbox("Health outcome", outcomes, index=outcomes.index("Diabetes"))
scope = st.radio("Counties to include", [f"{state} only", "All states"], horizontal=True)

#Put the two measures side by side, one row per county
pair = places[places["measure"].isin([need, outcome])]
if scope != "All states":
    pair = pair[pair["state_name"] == state]
pair = pair.pivot_table(index=["state", "county"], columns="measure", values="value")
pair = pair.reindex(columns=[need, outcome]).dropna().reset_index()
pair.columns = ["state", "county", "need", "outcome"]

if len(pair) == 0:
    st.warning(f"{state} has no social needs estimates. Choose \"All states\" to see the national pattern.")
elif len(pair) < 3:
    st.warning(f"Too few {state} counties to compare. Choose \"All states\" to see the national pattern.")
else:
    scatter = (
        alt.Chart(pair)
        .mark_circle(opacity=0.5)
        .encode(
            alt.X("need:Q", title=f"{need} (%)"),
            alt.Y("outcome:Q", title=f"{outcome} (%)"),
            tooltip=["county", "state", "need", "outcome"]
        )
    )
    st.altair_chart(scatter, width="stretch")
    col1, col2 = st.columns(2)
    col1.metric("Counties", len(pair))
    col2.metric("Correlation (Pearson r)", f"{pair['need'].corr(pair['outcome']):.2f}")
    st.caption("Correlation does not mean causation. These are county estimates, so they do not "
               "describe individual people. PLACES estimates every measure from the same inputs (age, sex, "
               "race and ethnicity, education, and county poverty), which can make correlations look stronger.")
