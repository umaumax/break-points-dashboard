#!/usr/bin/env python3

import re
from io import StringIO

import streamlit as st
import pandas as pd
import plotly.express as px

st.title("Weekly Activity Aggregation (Plotly)")

input_method = st.radio("Select data input method",
                        ("Text Input on Web", "File Upload"))

# Mapping for day abbreviations in Japanese and English
day_mapping = {
    "Mon": "Mon", "Tue": "Tue", "Wed": "Wed", "Thu": "Thu", "Fri": "Fri",
    "月": "Mon", "火": "Tue", "水": "Wed", "木": "Thu", "金": "Fri",
}

if input_method == "File Upload":
    uploaded_file = st.file_uploader(
        "Upload data file (JSON format)", type=["json"])
    if uploaded_file is not None:
        data = pd.read_json(StringIO(uploaded_file))
else:
    default_text = """
# 2024/11/25-29
* GitHub: 月.....火...水.木...金........
* JIRA: 月..火.............水.....木金.
* Confluence: 月.火水木..金
* slack: 月...火....水.....木.金...
* teams: 月..火.水....木.金.....
* 平均 5-10min

# 2024/12/02-06
* GitHub: 月....火...水..木..金...
* JIRA: 月..火....水......木.....金.
* Confluence: 月..火水木金
* slack: 月. 火...水..木...金.
* teams: 月火水木.金...
* pptx: 月...火水木金
* outlook: 月.火水木金

# 2024/12/09-13
* GitHub: 月...火水...木..金......
* JIRA: 月....火...水..木.......金....
* Confluence: 月火水木金.
* slack: 月.火水.木金
* teams: 月...火水.木金
* pptx: 月火水木金
* outlook: 月火.水木金
    """
    input_text = st.text_area(
        "Enter data (JSON format)",
        default_text,
        height=300)
    try:
        def parse_input(input_str):
            data = {}

            lines = input_str.strip().split("\n")

            current_week = None
            for line in lines:
                week_match = re.match(r"[#\s]*(\d{4}/\d{2}/\d{2}-\d{2})", line)
                print(line, week_match)
                if week_match:
                    current_week = week_match.group(1)
                    data[current_week] = {}

                tool_match = re.match(r"\s*\* (.+): (.+)", line)
                if tool_match and current_week:
                    tool_name = tool_match.group(1).strip()
                    value = tool_match.group(2).strip()
                    data[current_week][tool_name] = value

            return data

        data = parse_input(input_text)
        # data = pd.read_json(StringIO(input_text)).to_dict()
    except ValueError:
        st.error("Invalid JSON format. Please correct and try again.")
        data = None

if data is not None:
    weeks = []
    for week, activities in data.items():
        for category, value in activities.items():
            text = str(value)
            day = "Unknown"
            count = 0
            offset = 0
            for day in day_mapping:
                if text.startswith(day):
                    text = text.removeprefix(day)
                    orig_length = len(text)
                    text = text.lstrip('.')
                    count = orig_length - len(text)
                    day = day_mapping[day]
                    weeks.append({
                        "week": week,
                        "category": category,
                        "day": day,
                        "activity": count,
                    })

    df = pd.DataFrame(weeks)

    with st.expander("parsed input data"):
        st.write("dict")
        st.write(data)

        st.write("data frame")
        st.write(df)

    category_order = df["category"].drop_duplicates()
    day_order = df["day"].drop_duplicates()

    selected_week = st.selectbox("Select week to display", df["week"].unique())

    filtered_data = df[df["week"] == selected_week]

    st.subheader(f"{selected_week} per app")
    bar_fig = px.bar(filtered_data, x="category", y="activity", title=f"{selected_week} per app", color="day",
                     labels={"category": "Apps", "activity": "Counts"}, text="activity", color_discrete_sequence=px.colors.qualitative.D3)
    st.plotly_chart(bar_fig)

    st.subheader(f"{selected_week} per day")
    bar_fig = px.bar(filtered_data, x="day", y="activity", title=f"{selected_week} per day", color="category",
                     labels={"category": "Day", "activity": "Counts"}, text="activity", color_discrete_sequence=px.colors.qualitative.Antique)
    st.plotly_chart(bar_fig)

    st.subheader("Overall Heatmap")
    pivot_data = df.pivot_table(
        index="week",
        columns="category",
        values="activity",
    ).fillna(0).reindex(columns=category_order)
    heatmap_fig = px.imshow(pivot_data, text_auto=True, color_continuous_scale="YlGnBu",
                            title="Activity Count per week by Apps (Heatmap)", labels=dict(color="Activity Count"))
    st.plotly_chart(heatmap_fig)

    pivot_data = df.pivot_table(
        columns="category",
        values="activity",
        aggfunc="sum",
    ).fillna(0).reindex(columns=category_order)
    heatmap_fig = px.imshow(pivot_data, text_auto=True, color_continuous_scale="YlGnBu",
                            title="Activity Count by Apps (Heatmap)", labels=dict(color="Activity Count"))
    st.plotly_chart(heatmap_fig)

    pivot_data = df.pivot_table(
        index="week",
        columns="day",
        values="activity",
        fill_value=0,
    ).reindex(columns=day_order)
    heatmap_fig = px.imshow(pivot_data, text_auto=True, color_continuous_scale="YlGnBu",
                            title="Activity Count per week by Day (Heatmap)", labels=dict(color="Activity Count"))
    st.plotly_chart(heatmap_fig)

    pivot_data = df.pivot_table(
        columns="day",
        values="activity",
        aggfunc="sum",
        fill_value=0,
    ).reindex(columns=day_order)
    heatmap_fig = px.imshow(pivot_data, text_auto=True, color_continuous_scale="YlGnBu",
                            title="Activity Count by Day (Heatmap)", labels=dict(color="Activity Count"))
    st.plotly_chart(heatmap_fig)
