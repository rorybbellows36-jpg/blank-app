# asset_inspections_dashboard.py

import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3  # or use other DB connector if needed
from datetime import datetime

# ---------- SETTINGS ----------
st.set_page_config("Asset Inspection Dashboard", layout="wide")

# ---------- DATA LOADING ----------

@st.cache_data
def load_csv_data(file):
    df = pd.read_csv(file, parse_dates=["inspection_date", "due_date"])
    return df

@st.cache_data
def load_sql_data(db_path, table_name="inspections"):
    conn = sqlite3.connect(db_path)
    df = pd.read_sql(f"SELECT * FROM {table_name}", conn, parse_dates=["inspection_date", "due_date"])
    conn.close()
    return df

data_source = st.sidebar.selectbox("Select Data Source", ["CSV", "SQL Database"])

if data_source == "CSV":
    uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
    if uploaded_file:
        df = load_csv_data(uploaded_file)
    else:
        st.stop()

else:  # SQL
    db_path = st.sidebar.text_input("SQLite DB Path")
    table_name = st.sidebar.text_input("Table Name", value="inspections")
    if db_path:
        df = load_sql_data(db_path, table_name)
    else:
        st.stop()

# ---------- DATA FILTERS ----------

st.sidebar.markdown("### Filters")

# Optional filters if those columns exist
if "asset_type" in df.columns:
    asset_types = st.sidebar.multiselect("Asset Type", options=df["asset_type"].unique(), default=df["asset_type"].unique())
    df = df[df["asset_type"].isin(asset_types)]

if "site" in df.columns:
    sites = st.sidebar.multiselect("Site", options=df["site"].unique(), default=df["site"].unique())
    df = df[df["site"].isin(sites)]

if "inspector" in df.columns:
    inspectors = st.sidebar.multiselect("Inspector", options=df["inspector"].unique(), default=df["inspector"].unique())
    df = df[df["inspector"].isin(inspectors)]

# Date range filter
if "inspection_date" in df.columns:
    min_date, max_date = df["inspection_date"].min(), df["inspection_date"].max()
    date_range = st.sidebar.date_input("Inspection Date Range", [min_date, max_date])
    df = df[(df["inspection_date"] >= pd.to_datetime(date_range[0])) & (df["inspection_date"] <= pd.to_datetime(date_range[1]))]

# ---------- KPIs ----------

total_inspections = len(df)
pass_rate = (df["status"] == "Passed").sum() / total_inspections * 100
fail_rate = (df["status"] == "Failed").sum() / total_inspections * 100
overdue_count = (df["due_date"] < df["inspection_date"]).sum()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Inspections", total_inspections)
col2.metric("Pass Rate (%)", f"{pass_rate:.1f}%")
col3.metric("Fail Rate (%)", f"{fail_rate:.1f}%")
col4.metric("Overdue Inspections", overdue_count)

# ---------- CHARTS ----------

st.markdown("### Inspection Outcomes")
outcome_chart = px.pie(df, names="status", title="Inspection Status Breakdown")
st.plotly_chart(outcome_chart, use_container_width=True)

st.markdown("### Inspections Over Time")
inspections_by_month = df.resample('M', on='inspection_date').size().reset_index(name='count')
line_chart = px.line(inspections_by_month, x='inspection_date', y='count', title='Inspections per Month')
st.plotly_chart(line_chart, use_container_width=True)

st.markdown("### Status by Asset Type")
bar_chart = px.bar(df.groupby(['asset_type', 'status']).size().reset_index(name='count'),
                   x='asset_type', y='count', color='status',
                   title='Inspection Results by Asset Type')
st.plotly_chart(bar_chart, use_container_width=True)

# ---------- DATA TABLE ----------
with st.expander("🔍 View Raw Data"):
    st.dataframe(df)
