# streamlit_climate_dashboard_final.py
import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import json

st.set_page_config(layout="wide")
st.title("US Counties in Most Need: Climate Risk, Perception & Resilience")

# -----------------------------
# 1. Load main dataset (includes FEMA fields)
# -----------------------------
DATA_CSV = "visual_data.csv"
df = pd.read_csv(DATA_CSV, low_memory=False)
df.columns = df.columns.str.strip()

# Ensure FIPS codes are strings with leading zeros
df["county_fips"] = df["county_fips"].fillna('00000').astype(str).str.zfill(5)

# Avoid NAs
num_cols = ["happening","candidatevotes","totalvotes","risk_score","resl_score"]
for col in num_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

# -----------------------------
# 2. Perceived Risk
# -----------------------------
PERCEIVED_COL = "happening"
df[PERCEIVED_COL] = pd.to_numeric(df[PERCEIVED_COL], errors="coerce")
base = df.groupby("county_fips", as_index=False).agg({
    PERCEIVED_COL: "mean"
}).rename(columns={PERCEIVED_COL: "PerceivedRisk"})

# -----------------------------
# 3. Compute Party Vote Percentages
# -----------------------------
elec_cols = ["county_fips","party","candidatevotes","totalvotes"]
elec = df[elec_cols].dropna()

elec["candidatevotes"] = pd.to_numeric(elec["candidatevotes"], errors="coerce").fillna(0)
elec["totalvotes"] = pd.to_numeric(elec["totalvotes"], errors="coerce").replace(0, pd.NA)
elec = elec[elec["totalvotes"].notna()]

elec["vote_pct"] = elec["candidatevotes"] / elec["totalvotes"]

party_share = (
    elec.groupby(["county_fips","party"])["vote_pct"]
    .sum()
    .reset_index()
)

party_pivot = party_share.pivot(index="county_fips", columns="party", values="vote_pct").reset_index()
party_pivot = party_pivot.fillna(0)

# Rename parties
rename_map = {}
for col in party_pivot.columns:
    c = col.lower()
    if c in ("democrat","democratic","dem"):
        rename_map[col] = "DemVotePct"
    if c in ("republican","rep","gop"):
        rename_map[col] = "RepVotePct"

party_pivot = party_pivot.rename(columns=rename_map)
party_pivot["DemVotePct"] = party_pivot.get("DemVotePct", 0)
party_pivot["RepVotePct"] = party_pivot.get("RepVotePct", 0)

# Merge votes with base
base = base.merge(party_pivot, on="county_fips", how="left")

# -----------------------------
# 4. Add FEMA Risk and Resilience
# -----------------------------
fema_cols = ["county_fips","risk_score","resl_score"]
fema = df[fema_cols].drop_duplicates(subset="county_fips").copy()
fema["TotalRiskScore"] = pd.to_numeric(fema["risk_score"], errors="coerce")
fema["ResilienceScore"] = pd.to_numeric(fema["resl_score"], errors="coerce")

# Merge with base
merged = base.merge(fema[["county_fips","TotalRiskScore","ResilienceScore"]], on="county_fips", how="left")

# -----------------------------
# 5. Compute RiskGap and Enhanced NeedScore
# -----------------------------
merged["RiskGap"] = merged["TotalRiskScore"] - merged["PerceivedRisk"]

# Streamlit sliders for political & resilience weighting
st.sidebar.header("Filters & Settings")

weight = st.sidebar.slider(
    "Political Weighting: 0 = Dem, 1 = Rep",
    min_value=0.0, max_value=1.0, value=1.0, step=0.01
)
res_weight = st.sidebar.slider(
    "Resilience Weighting: 0 = ignore, 1 = full effect",
    min_value=0.0, max_value=1.0, value=1.0, step=0.01
)

merged["WeightedPolitical"] = (
    weight * merged["RepVotePct"] + (1-weight) * merged["DemVotePct"]
) / 100

# Normalize resilience factor (0-1, inverted: low resilience → higher need)
merged["ResilienceFactor"] = 1 - (merged["ResilienceScore"] / merged["ResilienceScore"].max())

merged["NeedScore"] = merged["RiskGap"] * merged["WeightedPolitical"]
merged["EnhancedNeedScore"] = merged["NeedScore"] * (1 + res_weight * merged["ResilienceFactor"])

# -----------------------------
# 6. State filter
# -----------------------------
states = df['state'].unique()
selected_state = st.sidebar.selectbox("Select a State", states)
data = merged[merged['county_fips'].isin(df[df['state']==selected_state]['county_fips'])].copy()

# -----------------------------
# 7. Load US county GeoJSON
# -----------------------------
counties = gpd.read_file("cb_2018_us_county_5m.geojson")

# Merge on COUNTYFP (ensure string)
counties["COUNTYFP"] = counties["COUNTYFP"].astype(str).str.zfill(5)
gdf = counties.merge(data, left_on='COUNTYFP', right_on='county_fips', how='left')

# Remove rows with empty geometries
gdf = gdf[~gdf.geometry.isna()]

# Convert to GeoJSON for Plotly
geojson_data = json.loads(gdf.to_json())

# -----------------------------
# 8. Choropleth map
# -----------------------------
st.subheader("US Counties by Enhanced NeedScore")
gdf['hover_text'] = (
    "County: " + gdf['NAME'] +
    "<br>State: " + selected_state +
    "<br>Actual Risk: " + gdf['TotalRiskScore'].astype(str) +
    "<br>Perceived Risk: " + gdf['PerceivedRisk'].astype(str) +
    "<br>Risk Gap: " + gdf['RiskGap'].round(2).astype(str) +
    "<br>Resilience Score: " + gdf['ResilienceScore'].round(2).astype(str) +
    "<br>Dem Vote %: " + gdf['DemVotePct'].round(1).astype(str) +
    "<br>Rep Vote %: " + gdf['RepVotePct'].round(1).astype(str) +
    "<br>Enhanced NeedScore: " + gdf['EnhancedNeedScore'].round(2).astype(str)
)

fig_map = px.choropleth_mapbox(
    gdf,
    geojson=geojson_data,
    locations='county_fips',
    featureidkey="properties.county_fips",
    color='EnhancedNeedScore',
    hover_name='hover_text',
    color_continuous_scale='Reds',
    mapbox_style="carto-positron",
    zoom=3,
    center={"lat": 37.0902, "lon": -95.7129}
)
st.plotly_chart(fig_map, use_container_width=True)

# -----------------------------
# 9. Scatterplot: RiskGap vs Political Affiliation
# -----------------------------
st.subheader("Scatterplot: RiskGap vs Political Affiliation")
data['hover_text'] = (
    "County: " + data['county_fips'] +
    "<br>Actual Risk: " + data['TotalRiskScore'].astype(str) +
    "<br>Perceived Risk: " + data['PerceivedRisk'].astype(str) +
    "<br>Risk Gap: " + data['RiskGap'].round(2).astype(str) +
    "<br>Resilience Score: " + data['ResilienceScore'].round(2).astype(str) +
    "<br>Dem Vote %: " + data['DemVotePct'].round(1).astype(str) +
    "<br>Rep Vote %: " + data['RepVotePct'].round(1).astype(str) +
    "<br>Enhanced NeedScore: " + data['EnhancedNeedScore'].round(2).astype(str)
)

fig_scatter = px.scatter(
    data,
    x='DemVotePct',
    y='RiskGap',
    color='EnhancedNeedScore',
    hover_name='hover_text',
    color_continuous_scale='Reds'
)
st.plotly_chart(fig_scatter, use_container_width=True)

# -----------------------------
# 10. Top 20 counties table
# -----------------------------
st.subheader("Top 20 Counties by Enhanced NeedScore")
top_counties = data.sort_values('EnhancedNeedScore', ascending=False).head(20)
st.dataframe(top_counties[['county_fips','TotalRiskScore','PerceivedRisk','DemVotePct','RepVotePct','ResilienceScore','RiskGap','EnhancedNeedScore']])

# -----------------------------
# 11. Download CSV
# -----------------------------
st.download_button(
    label="Download Top 20 Counties CSV",
    data=top_counties.to_csv(index=False),
    file_name='top_counties_enhanced.csv',
    mime='text/csv'
)
