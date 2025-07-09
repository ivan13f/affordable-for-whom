import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.graph_objects as go
import plotly.express as px
import json
from data_loader import load_rents_BEZ, load_rents_PLR, load_income_persons, load_income_households, load_plr_geo

rents_BEZ = load_rents_BEZ()
rents_PLR = load_rents_PLR()
income_persons = load_income_persons()
income_households = load_income_households()
plr_geo = load_plr_geo()

def show_affordability_tab():
    st.markdown("## Affordability Analysis")
    st.markdown("---")
    
    col1, col2 = st.columns([2, 5])    
    with col1:
        st.markdown("## Rents have risen faster than incomes, resulting in a rent burden of 34% for the average tenant in 2023.")
        st.markdown('<p>This is still without accounting for housing expenses and heating.</p>', unsafe_allow_html=True)
        st.markdown('<p>Despite a slight dip during the pandemic, the rent burden continues to climb.</p>', unsafe_allow_html=True)
    with col2:
        st.markdown("###### Median Montly Disposable Income vs Median Rent")
        rents_by_year = rents_BEZ.groupby('year')['median'].mean().reset_index()
        income_df = income_persons[income_persons["year"].between(2013, 2023)].copy()
        income_df.rename(columns={"monthly_disposable_income": "monthly_available_income"}, inplace=True)

        combined = pd.merge(
            rents_by_year[rents_by_year['year'].between(2013, 2023)],
            income_df[['year', 'monthly_available_income']],
            on='year',
            how='inner'
        )

        combined['rent_1R'] = (combined['median'] * 50).round(0)
        combined['rent_burden'] = (combined['rent_1R'] / combined['monthly_available_income'] * 100).round(0)

        income_color = "#8F8F8F"   # light grey
        rent_color = "#D4583B"     # strong orange
        burden_color = "#D4583B"   # same orange for dashed line

        # Create figure
        fig_burden = go.Figure()

        # Area: Rent
        fig_burden.add_trace(go.Scatter(
            x=combined["year"],
            y=combined["rent_1R"],
            name="1R Apartment Rent",
            fill="tonexty",
            fillcolor=rent_color,
            mode="lines+markers",
            line=dict(color=rent_color),
            marker=dict(size=6),
            yaxis="y1",
            hovertemplate="1R Apartment Rent<br>Year: %{x}<br>€ %{y:.0f}<extra></extra>"
        ))

        # Area: Income
        fig_burden.add_trace(go.Scatter(
            x=combined["year"],
            y=combined["monthly_available_income"],
            name="Available Income",
            fill="tonexty",
            mode="lines+markers",
            line=dict(color=income_color),
            marker=dict(size=6),
            yaxis="y1",
            hovertemplate="Monthly Median Income<br>Year: %{x}<br>€ %{y:.0f}<extra></extra>"
            ))

        # Line: Rent Burden
        fig_burden.add_trace(go.Scatter(
            x=combined["year"],
            y=combined["rent_burden"],
            name="Rent Burden (%)",
            mode="lines+markers+text",
            line=dict(color=burden_color),
            marker=dict(size=6, color=burden_color),
            text=["" if year in [2013, 2023] else f"{int(v)}%" for year, v in zip(combined["year"], combined["rent_burden"])],
            textposition="top center",
            textfont=dict(color=burden_color, size=13, family="Arial Black"),
            yaxis="y2",
            hovertemplate="Rent Burden<br>Year: %{x}<br>%{y:.0f}%<extra></extra>"
        ))

        # Layout styling
        fig_burden.update_layout(
            height=600,
            plot_bgcolor="white",
            paper_bgcolor="white",
            xaxis=dict(
                title=None,
                tickmode="linear",
                dtick=1,
                linecolor="black",
                showline=True,
                tickfont=dict(size=14, color="black"),
                range=[2013, 2023]
            ),
            yaxis=dict(
                title="€ per Month",
                showline=True,
                showgrid=False,
                linecolor="black",
                tickfont=dict(color="black"),
                rangemode="tozero"
            ),
            yaxis2=dict(
                title="Rent Burden (%)",
                overlaying="y",
                side="right",
                showline=True,
                showgrid=False,
                linecolor="black",
                tickfont=dict(color="black"),
                range=[0, 45]
            ),
            legend=dict(
                x=0.01, y=0.99,
                font=dict(size=16, color="black")
            ),
            hoverlabel=dict(font_size=16, font_family="Arial", font_color="black"),
            margin=dict(l=60, r=60, t=40, b=60)
        )

        # Adjusted annotations to avoid being cut off
        fig_burden.add_annotation(
            x=2013.3,
            y=combined.loc[combined["year"] == 2013, "rent_burden"].values[0],
            text=f"{int(combined.loc[combined['year'] == 2013, 'rent_burden'].values[0])}%",
            showarrow=False,
            xanchor="center",
            yanchor="bottom",
            font=dict(color="#D4583B", size=13, family="Arial Black"),
            yref="y2"
        )

        fig_burden.add_annotation(
            x=2022.7,
            y=combined.loc[combined["year"] == 2023, "rent_burden"].values[0],
            text=f"{int(combined.loc[combined['year'] == 2023, 'rent_burden'].values[0])}%",
            showarrow=False,
            xanchor="center",
            yanchor="bottom",
            font=dict(color="#D4583B", size=13, family="Arial Black"),
            yref="y2"
        )
        st.plotly_chart(fig_burden, use_container_width=True)

    st.markdown("---")

    col1, col2 = st.columns([2, 5])

    with col1:
        st.markdown("## There are 232 PLRs where 1-Room-Apartment would be considered affordable for the median income earner.")
        st.markdown("Central areas has become increasingly unaffordable, with certain exceptions to be analysed in detail.")
        st.markdown("**Asummptions:**\n- Average median available income 2023: 2031 €/month.\n- Size 1-room-apartment: 50m².")
      

    with col2:
        st.markdown("###### Rent Burden by PLR 2023 (Median Income Earner, 1R Apartment)")

        col1, col2 = st.columns([10, 1])
        
        with col1:
            # Get median income for Berlin 2023
            income_2023 = income_households[income_households["year"] == 2023]["monthly_available_income"].values[0]

            # Filter rent prices for 2023 and calculate 1R rent & rent burden
            rents_2023 = rents_PLR[rents_PLR["year"] == 2023][["plr_id", "median"]].copy()
            rents_2023["rent_1R"] = rents_2023["median"] * 50
            rents_2023["rent_burden"] = rents_2023["rent_1R"] / income_2023

            # Merge with geometry
            geo_merged = plr_geo.merge(rents_2023, on="plr_id", how="left")
            gdf_median = gpd.GeoDataFrame(geo_merged, geometry="geometry", crs="EPSG:4326")

            # Convert to GeoJSON
            geojson_dict = json.loads(gdf_median.to_json())

            # Define color scale
            custom_scale = [
                [0.00, "#e0f3db"],  # very light green (very affordable)
                [0.15, "#a8ddb5"],  # medium green
                [0.30, "#41b17a"],  # deep green (affordability threshold)
                [0.40, "#fecc5c"],  # yellow
                [0.50, "#fd8d3c"],  # orange
                [0.60, "#f03b20"],  # red-orange
                [1.00, "#bd0026"]   # dark red
            ]
            range_vals = [0, 0.6]

            # Choropleth map
            fig_afford_median = px.choropleth_mapbox(
                gdf_median,
                geojson=geojson_dict,
                locations="plr_id",
                featureidkey="properties.plr_id",
                color="rent_burden",
                color_continuous_scale=custom_scale,
                range_color=range_vals,
                center={"lat": 52.52, "lon": 13.405},
                zoom=10,
                mapbox_style="carto-positron",
                opacity=0.8,
                hover_name="plr_name",
                hover_data={
                    "plr_id": False,
                    "rent_burden": ':.1%',
                    "rent_1R": ':.0f',
                }
            )

            # Customization
            fig_afford_median.update_traces(
                customdata=gdf_median[["rent_1R", "rent_burden"]],
                hovertext=gdf_median["plr_name"],
                hovertemplate="<b>%{hovertext}</b><br>" +
                            "Rent 1R Apt.: %{customdata[0]:.0f} €<br>" +
                            "Rent Burden: %{customdata[1]:.1%}<extra></extra>",
                hoverlabel=dict(
                    font_size=16,
                    font_family="Inter"
                )
            )
            # Styling
            fig_afford_median.update_layout(
                height=800,
                margin=dict(r=0, t=0, l=0, b=0),
                coloraxis_colorbar=dict(
                    title="Rent Burden %",
                    tickmode="array",
                    tickvals=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
                    ticktext=["0%", "10%", "20%", "30%", "40%", "50%", "60%"],
                    tickfont=dict(size=14),
                    len=0.3,
                    y= 0.05,
                    x=0.01,
                    xanchor="left",
                    yanchor="bottom"
                )
            )

            # Grey boundaries
            fig_afford_median.update_traces(marker_line_color="gray", marker_line_width=0.5)

            st.plotly_chart(fig_afford_median, use_container_width=True)

        with col2:
            # Binning based on rent burden for average median income
            bins_income = {
                "0–15%": {"count": (gdf_median["rent_burden"] <= 0.15).sum(), "color": "#e0f3db"},
                "15–30%": {"count": ((gdf_median["rent_burden"] > 0.15) & (gdf_median["rent_burden"] < 0.30)).sum(), "color": "#a8ddb5"},
                "30%": {"count": (gdf_median["rent_burden"] == 0.30).sum(), "color": "#41b17a"},
                "30–40%": {"count": ((gdf_median["rent_burden"] > 0.30) & (gdf_median["rent_burden"] < 0.40)).sum(), "color": "#fecc5c"},
                "40–50%": {"count": ((gdf_median["rent_burden"] >= 0.40) & (gdf_median["rent_burden"] < 0.50)).sum(), "color": "#fd8d3c"},
                "50–60%": {"count": ((gdf_median["rent_burden"] >= 0.50) & (gdf_median["rent_burden"] < 0.60)).sum(), "color": "#f03b20"},
                "60%+": {"count": (gdf_median["rent_burden"] >= 0.60).sum(), "color": "#bd0026"},
            }

            # Filter out zero-count categories
            bins_income = {k: v for k, v in bins_income.items() if v["count"] > 0}

            # Build chart
            bars_income = []
            annotations_income = []
            y_offset = 0
            for label, bin_data in bins_income.items():
                count = bin_data["count"]
                bars_income.append(go.Bar(
                    x=["PLRs"],
                    y=[count],
                    marker=dict(color=bin_data["color"]),
                    width=1,
                    name=label,
                    hovertemplate=f"{label}: {count} PLRs<extra></extra>",
                    showlegend=False
                ))
                annotations_income.append(dict(
                    x="PLRs",
                    y=y_offset + count / 2,
                    text=str(count),
                    showarrow=False,
                    font=dict(color="white", size=18),
                    xanchor="center",
                    yanchor="middle"
                ))
                y_offset += count

            fig_income_bar = go.Figure(data=bars_income)
            fig_income_bar.update_layout(
                barmode="stack",
                height=800,
                margin=dict(t=0, b=0, l=0, r=0),
                plot_bgcolor="white",
                paper_bgcolor="white",
                annotations=annotations_income,
                xaxis=dict(
                    showticklabels=False,
                    showgrid=False,
                    showline=False,
                    zeroline=False,
                    fixedrange=True
                ),
                yaxis=dict(
                    range=[0, y_offset],
                    showticklabels=False,
                    showgrid=False,
                    showline=False,
                    zeroline=False,
                    fixedrange=True
                )
            )
            st.plotly_chart(fig_income_bar, use_container_width=True)

    st.markdown("---")


    col1, col2 = st.columns([2, 5])

    with col1:
        st.markdown("## But only 15 for the Social Welfare recipient")
        st.markdown("The areas that are considered affordable are few and relayed to the outskirts.")
        st.markdown("**Asummptions:**\n- Maximum coverage of cold rent for 1 person: 426 €/month.\n- Heating costs and Utilities: 50-70 €/month.\n- Monthly Allowance: 563 €/month.\n- Maximum 1-room-apartment size accepted: 50m².")

    with col2:    
        st.markdown("###### Rent Burden by PLR 2023 (Social Welfare Recipient, 1R Apartment)")

        col1, col2 = st.columns([10, 1])
            
        with col1:
            income_buergergeld = 1143

            # 1. Filter rent prices for 2023 and calculate rent + burden
            rents_2023_bg = rents_PLR[rents_PLR["year"] == 2023][["plr_id", "median"]].copy()
            rents_2023_bg["rent_1R"] = rents_2023_bg["median"] * 50
            rents_2023_bg["rent_burden"] = rents_2023_bg["rent_1R"] / income_buergergeld

            # 2. Merge with geometry
            geo_bg = plr_geo.merge(rents_2023_bg, on="plr_id", how="left")
            gdf_bg = gpd.GeoDataFrame(geo_bg, geometry="geometry", crs="EPSG:4326")
            geojson_bg = json.loads(gdf_bg.to_json())

            # 4. Plot
            fig_afford_bg = px.choropleth_mapbox(
                gdf_bg,
                geojson=geojson_bg,
                locations="plr_id",
                featureidkey="properties.plr_id",
                color="rent_burden",
                color_continuous_scale=custom_scale,
                range_color=[0, 0.6],
                center={"lat": 52.52, "lon": 13.405},
                zoom=10,
                mapbox_style="carto-positron",
                opacity=0.8,
                hover_name="plr_name",
                hover_data={
                    "plr_id": False, 
                    "rent_burden": ':.1%',
                    "rent_1R": ':.0f',
                }
            )

            # 5. Customize hover text with order, formatting, and styling
            fig_afford_bg.update_traces(
                customdata=gdf_bg[["rent_1R", "rent_burden"]],
                hovertext=gdf_bg["plr_name"],
                hovertemplate="<b>%{hovertext}</b><br>" +
                            "Rent 1R Apt.: %{customdata[0]:.0f} €<br>" +
                            "Rent Burden: %{customdata[1]:.1%}<extra></extra>",
                hoverlabel=dict(
                    font_size=16,
                    font_family="Inter"
                )
            )

            # 6. Layout
            fig_afford_bg.update_layout(
                height=800,
                margin=dict(r=0, t=0, l=0, b=0),
                coloraxis_colorbar=dict(
                    title="Rent Burden %",
                    tickmode="array",
                    tickvals=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
                    ticktext=["0%", "10%", "20%", "30%", "40%", "50%", "60%"],
                    tickfont=dict(size=14),
                    len=0.3,
                    y=0.05,
                    x=0.01,
                    xanchor="left",
                    yanchor="bottom"
                )
            )

            fig_afford_bg.update_traces(marker_line_color="gray", marker_line_width=0.5)

            st.plotly_chart(fig_afford_bg, use_container_width=True)

        with col2:
            # Custom scale bins with counts (remove bins with count 0)
            bin_counts_custom = [
                {"label": "15–30%", "count": 4, "color": "#a8ddb5"},
                {"label": "30%", "count": 11, "color": "#41b17a"},
                {"label": "30–40%", "count": 28, "color": "#fecc5c"},
                {"label": "40–50%", "count": 95, "color": "#fd8d3c"},
                {"label": "50–60%", "count": 172, "color": "#f03b20"},
                {"label": "60%+", "count": 232, "color": "#bd0026"},
            ]

            # Filter out bins with 0 counts
            bin_counts_custom = [b for b in bin_counts_custom if b["count"] > 0]

            # Build the bar and annotation lists
            bars = []
            annotations = []
            y_offset = 0
            for b in bin_counts_custom:
                bars.append(go.Bar(
                    x=["PLRs"],
                    y=[b["count"]],
                    marker=dict(color=b["color"]),
                    width=1,
                    name=b["label"],
                    hovertemplate=f'{b["label"]}: {b["count"]} PLRs<extra></extra>',
                    showlegend=False
                ))
                annotations.append(dict(
                    x="PLRs",
                    y=y_offset + b["count"] / 2,
                    text=str(b["count"]),
                    showarrow=False,
                    font=dict(color="white", size=20),
                    xanchor="center",
                    yanchor="middle"
                ))
                y_offset += b["count"]

            # Create the figure
            bar_bg = go.Figure(data=bars)
            bar_bg.update_layout(
                barmode="stack",
                height=800,
                margin=dict(t=0, b=0, l=0, r=0),
                plot_bgcolor="white",
                paper_bgcolor="white",
                annotations=annotations,
                xaxis=dict(
                    showticklabels=False,
                    showgrid=False,
                    showline=False,
                    zeroline=False,
                    fixedrange=True
                ),
                yaxis=dict(
                    range=[0, y_offset],
                    showticklabels=False,
                    showgrid=False,
                    showline=False,
                    zeroline=False,
                    fixedrange=True
                )
            )
            st.plotly_chart(bar_bg, use_container_width=True)

    st.markdown("---")