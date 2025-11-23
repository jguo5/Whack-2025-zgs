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

par
