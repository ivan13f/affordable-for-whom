import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.graph_objects as go
import plotly.express as px
import json
from data_loader import load_wohnatlas_2022, load_wbs_berlin, load_subsidies, load_sh_subsidized_totals, load_pgr_geo

def show_social_tab():
    
    wohnatlas_2022 = load_wohnatlas_2022()
    wbs_berlin = load_wbs_berlin()
    subsidies = load_subsidies()
    sh_subsidized_totals = load_sh_subsidized_totals()
    pgr_geo = load_pgr_geo()

    st.markdown("## Access to Social & Subsidized Housing")
    st.markdown("---")

    st.markdown("## Welfare recipients are concentrated in specific districts, and the number of WBS certificates issued has grown alongside rising rents — reflecting increasing pressure on the city’s affordable housing system.")
    
    col1, col2 = st.columns([1,1])

    with col1:
        st.markdown("###### Proportion of Social Welfare Recipients by PGR (2022)")

        wohnatlas_2022.rename(columns=lambda x: x.strip(), inplace=True)
        wohnatlas_cleaned = wohnatlas_2022.drop(columns=["pgr_name"])
        wohnatlas_cleaned["anteil_leistungsempfaenger"] = (wohnatlas_cleaned["anteil_leistungsempfaenger"] / 100)
        wohnatlas_cleaned["anteil_sozialwohng_2022"] = (wohnatlas_cleaned["anteil_sozialwohng_2022"] / 100)
        merged_pgr = pgr_geo.merge(
            wohnatlas_cleaned[["pgr_id", "anteil_leistungsempfaenger", "anteil_sozialwohng_2022"]],
            on="pgr_id",
            how="left")
        geojson_pgr = json.loads(merged_pgr.to_json())

        custom_orange_scale = [
            [0.00, "#FFF5F0"],
            [0.25, "#FDBBA6"],
            [0.50, "#FC8A6A"],
            [0.75, "#F15842"],
            [1.00, "#D4583B"]]

        # Choropleth map
        map_welfare = px.choropleth_mapbox(
            merged_pgr,
            geojson=geojson_pgr,
            locations="pgr_id",
            featureidkey="properties.pgr_id",
            color="anteil_leistungsempfaenger",
            color_continuous_scale=custom_orange_scale,
            range_color=[0, merged_pgr["anteil_leistungsempfaenger"].max()],
            mapbox_style="carto-positron",
            center={"lat": 52.52, "lon": 13.405},
            zoom=9,
            opacity=0.8,
            hover_name="pgr_name",
            hover_data={
                "pgr_id": False,
                "anteil_leistungsempfaenger": ':.1%'},
                labels={
                "anteil_leistungsempfaenger": "Social Welfare Receipients"}
        )

        #  Layout and colorbar styling
        map_welfare.update_layout(
            height=600,
            margin=dict(r=0, t=0, l=0, b=0),
            coloraxis_colorbar=dict(
                title="Social Welfare %",
                tickformat=".0%",
                title_font=dict(size=12),
                tickfont=dict(size=11),
                len=0.3,
                y=0.05,
                x=0.01,
                xanchor="left",
                yanchor="bottom"
            )
        )

        # Boundary lines
        map_welfare.update_traces(marker_line_color="gray", marker_line_width=0.5)

        st.plotly_chart(map_welfare, use_container_width=True)

    with col2:   
        st.markdown("###### WBS Recipients (2015–2024)")

        rename_map = {
            "1_person": "1 person",
            "2_person": "2 person",
            "3_person": "3 person",
            "4_person": "4 person",
            "5_person": "5 person",
            "5_or_more": "5 or more"}

        wbs_fixed = wbs_berlin[wbs_berlin["year"].between(2015, 2023)].copy()
        wbs_fixed["housing_type"] = wbs_fixed["housing_type"].replace(rename_map)

        # Set the order from 1 to 5 or more
        category_order = ["1 person", "2 person", "3 person", "4 person", "5 person", "5 or more"]
        wbs_fixed["housing_type"] = pd.Categorical(wbs_fixed["housing_type"], categories=category_order, ordered=True)

        # Pivot data
        pivot = wbs_fixed.pivot_table(index="year", columns="housing_type", values="amount", aggfunc="sum").fillna(0)
        pivot = pivot[category_order]  # Ensure correct order

        # Color gradient (darkest = 1 person, lightest = 5 or more)
        colors = ["#A33520", "#C84329", "#D4583B", "#EB9C7A", "#F3B39C", "#FCE0D9"]

        # 5. Create the stacked bar chart
        fig_wbs = go.Figure()

        for i, col in enumerate(pivot.columns):
            fig_wbs.add_trace(go.Bar(
                x=pivot.index,
                y=pivot[col],
                name=col,
                marker_color=colors[i],
                textposition="none"
            ))

        # 6. Add total annotations
        totals = pivot.sum(axis=1)
        for year, total in totals.items():
            fig_wbs.add_annotation(
                x=year,
                y=total,
                text=f"{int(total):,}",
                showarrow=False,
                yanchor="bottom",
                font=dict(size=13, color="#D4583B", family="Arial Black")
            )

        # 7. Layout styling
        fig_wbs.update_layout(
            barmode="stack",
            height=600,
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(l=60, r=60, t=40, b=40),
            xaxis=dict(
                title="Year",
                tickmode="linear",
                dtick=1,
                showline=True,
                linecolor="black",
                tickfont=dict(size=14, color="black")
            ),
            yaxis=dict(
                title="Number of WBS Recipients",
                showline=True,
                linecolor="black",
                tickfont=dict(color="black")
            ),
            legend=dict(
                title=None,
                font=dict(size=12, color="black"),
                traceorder="normal"
            )
        )

        st.plotly_chart(fig_wbs, use_container_width=True)

    st.markdown("---")

    st.markdown("## The distribution of subsidized housing only partially aligns with areas of greatest need, and with a 58% decline in units since 2015, the shrinking supply deepens spatial inequality in housing access.")

    col1, col2 = st.columns([1,1])
    with col1:   
        st.markdown("###### Proportion of subsidized housing by PGR (2022)")

        # Plot
        map_sh = px.choropleth_mapbox(
            merged_pgr,
            geojson=geojson_pgr,
            locations="pgr_id",
            featureidkey="properties.pgr_id",
            color="anteil_sozialwohng_2022",
            color_continuous_scale=custom_orange_scale,
            range_color=[0, merged_pgr["anteil_sozialwohng_2022"].max()],
            mapbox_style="carto-positron",
            center={"lat": 52.52, "lon": 13.405},
            zoom=9,
            opacity=0.8,
            hover_name="pgr_name",
            hover_data={
                "pgr_id": False,
                "anteil_sozialwohng_2022": ':.1%'},
                labels={
                "anteil_sozialwohng_2022": "Subsidized Housing"}
        )

        # Layout
        map_sh.update_layout(
            height=600,
            margin=dict(r=0, t=0, l=0, b=0),
            coloraxis_colorbar=dict(
                title="Subsidized Housing %",
                tickformat=".0%",
                title_font=dict(size=12),
                tickfont=dict(size=11),
                len=0.3,
                y=0.05,
                x=0.01,
                xanchor="left",
                yanchor="bottom"
            )
        )

        # Grey boundaries
        map_sh.update_traces(marker_line_color="gray", marker_line_width=0.5)

        st.plotly_chart(map_sh, use_container_width=True)

    with col2:   
        st.markdown("###### Total Subsidized Units (2015-2024)")

        # Bar chart of subsidized housing per year
        fig_subsidized = go.Figure()

        fig_subsidized.add_trace(go.Bar(
            x=subsidies["year"],
            y=subsidies["subsidized_housing"],
            marker_color="#D4583B",
            text=[f"{v:,}" for v in subsidies["subsidized_housing"]],
            textposition="outside",
            textfont=dict(color="black", size=12),
            name="New Subsidized Housing"
        ))

        # Layout styling
        fig_subsidized.update_layout(
            height=600,
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(l=60, r=60, t=40, b=40),
            xaxis=dict(
                title="Year",
                tickmode="linear",
                dtick=1,
                showline=True,
                linecolor="black",
                tickfont=dict(size=14, color="black")
            ),
            yaxis=dict(
                title="Units with New Subsidy",
                showline=True,
                linecolor="black",
                tickfont=dict(color="black")
            ),
            showlegend=False
        )

        st.plotly_chart(fig_subsidized, use_container_width=True)

    st.markdown("---")

    col1, col2 = st.columns([2,5])
    with col1:   
        st.markdown("## New construction by public housing companies falls short of demand.")
        st.markdown("Too few units are subjected to rent and access controls — widening the gap between housing need and available support.")

    with col2:   
        st.markdown("###### New Units by Public Housing Companies and % Subsidized")

        years = sh_subsidized_totals["year"]
        subsidised = sh_subsidized_totals["subsidised"]
        total_units = sh_subsidized_totals["total_units"]
        non_subsidised = total_units - subsidised
        percent_subsidised = (subsidised / total_units * 100).round(1)

        # Create figure
        fig_subsidized_bar = go.Figure()

        # Orange segment: Subsidized
        fig_subsidized_bar.add_trace(go.Bar(
            x=years,
            y=subsidised,
            name="Subsidized Units",
            marker_color="#D4583B"))

        # Grey segment: Non-Subsidized
        fig_subsidized_bar.add_trace(go.Bar(
            x=years,
            y=non_subsidised,
            name="Non-Subsidized Units",
            marker_color="lightgrey"))

        # Annotations on top of orange segment (%)
        for x, y, pct in zip(years, subsidised, percent_subsidised):
            fig_subsidized_bar.add_annotation(
                x=x,
                y=y + 200,
                text=f"{pct}%",
                showarrow=False,
                font=dict(color="#D4583B", size=13, family="Arial Black"),
                xanchor="center",
                yanchor="middle"
            )

        # Annotations on top of total bar (total count)
        for x, y in zip(years, total_units):
            fig_subsidized_bar.add_annotation(
                x=x,
                y=y + 200,
                text=f"{y:,}",
                showarrow=False,
                font=dict(color="grey", size=12, family="Arial"),
                xanchor="center"
            )

        # Layout
        fig_subsidized_bar.update_layout(
            barmode="stack",
            height=600,
            plot_bgcolor="white",
            paper_bgcolor="white",
            xaxis=dict(
                title="Year",
                tickmode="linear",
                dtick=1,
                linecolor="black",
                showline=True,
                tickfont=dict(size=14, color="black")
            ),
            yaxis=dict(
                title="New Housing Units",
                linecolor="black",
                showline=True,
                tickfont=dict(size=14, color="black")
            ),
            legend=dict(
                x=0.01, y=0.99,
                font=dict(size=12, color="black")
            ),
            margin=dict(l=60, r=60, t=40, b=40)
        )

        st.plotly_chart(fig_subsidized_bar, use_container_width=True)

    st.markdown("---")