import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Job Search Tracker", page_icon="📊", layout="wide")
st.title("📊 My Job Search Dashboard")

file_name = 'metrics.csv'

if not os.path.exists(file_name):
    st.warning("No real data found from the robot yet! Showing sample data...")
    fake_data = {
        "Date": ["2026-03-02", "2026-03-03", "2026-03-04"],
        "Applications": [15, 22, 10],
        "Rejections": [2, 4, 1],
        "Assessments": [0, 2, 1], # 📝 NEW: Assessment Data!
        "Uncertain": [1, 0, 2]
    }
    df = pd.DataFrame(fake_data)
else:
    df = pd.read_csv(file_name)

total_apps = df['Applications'].sum()
total_rejections = df['Rejections'].sum()
total_assessments = df['Assessments'].sum() # 📝 NEW: Count assessments

# 📝 NEW: 4 Columns instead of 3
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Applications", total_apps)
col2.metric("Total Assessments 💻", total_assessments)
col3.metric("Total Rejections", total_rejections)

if total_apps > 0:
    response_rate = round((total_rejections / total_apps) * 100, 1)
else:
    response_rate = 0
col4.metric("Rejection Rate", f"{response_rate}%")

st.divider()

st.subheader("Daily Activity Trend")
fig = px.bar(
    df, 
    x="Date", 
    # 📝 NEW: Add Assessments to the graph!
    y=["Applications", "Assessments", "Rejections", "Uncertain"], 
    barmode="group",
    color_discrete_map={
        "Applications": "#00CC96", # Green
        "Assessments": "#636EFA",  # Blue
        "Rejections": "#EF553B",   # Red
        "Uncertain": "#FFA15A"     # Orange
    }
)

st.plotly_chart(fig, use_container_width=True)