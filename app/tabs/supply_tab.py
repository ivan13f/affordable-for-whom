import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
import json
from data_loader import load_rents_PLR, load_rents_BEZ, load_plr_geo, load_rent_structure

rents_PLR = load_rents_PLR()
rents_BEZ = load_rents_BEZ()
rent_structure = load_rent_structure()
plr_geo = load_plr_geo()

def show_supply_tab():
    st.markdown("## Evolution of the Rental Market")
    st.markdown("---")

    col1, col2 = st.columns([2,5])
    with col1:
        st.markdown("## New rentals increased on average 80,31% in price since 2013, and the increase only acelerated since 2020.")
        st.markdown("Taking a look at the year-on-year increase in the average median price of new rentals, we see a rapid recovery after the COVID pandemic.")
        st.markdown("<div style='margin-top:40px'></div>", unsafe_allow_html=True)
        st.markdown('<p class="caption">* This is not the price that people pay, but the price of new listings. For that, it would be more useful to take a look at the Mietspiegel.</p>', unsafe_allow_html=True)
        st.markdown('<p class="caption">* "All Berlin" is calculated as the average of district-level medians.</p>', unsafe_allow_html=True)

    with col2:
        st.markdown("###### Average Median Rent Prices and Yearly Increases")

        # Clean up district names
        rents_BEZ["bez_name"] = rents_BEZ["bez_name"].str.strip()

        # Dropdown options
        districts = ["All Berlin"] + sorted(rents_BEZ["bez_name"].unique())
        selected_district_rent = st.selectbox("Choose a district", options=districts, key="selectbox_rent")

        # Filter data
        if selected_district_rent == "All Berlin":
            # Step 1: Calculate mean rent per district per year
            district_avg = (
                rents_BEZ[rents_BEZ["year"].between(2013, 2023)]
                .groupby(["year", "bez_name"])["median"]
                .mean()
                .reset_index()
            )

            # Step 2: Average across districts for each year
            filtered = (
                district_avg
                .groupby("year")["median"]
                .mean()
                .loc[2013:2023]
            )
        else:
            filtered = (
                rents_BEZ[
                    (rents_BEZ["bez_name"] == selected_district_rent) &
                    (rents_BEZ["year"].between(2013, 2023))
                ]
                .groupby("year")["median"]
                .mean()
                .loc[2013:2023]
            )

        # Calculate YoY % change
        yoy_pct_increase = (filtered.pct_change() * 100).round(2)

        # Create plot
        fig1 = go.Figure()

        fig1.add_trace(go.Bar(
            x=yoy_pct_increase.index,
            y=yoy_pct_increase.values,
            name="Yearly Increase (%)",
            marker_color="#D4583B",
            yaxis="y",
            text=[f"{v:.2f}%" if pd.notna(v) else "" for v in yoy_pct_increase],
            textposition="outside",
            textfont=dict(color="#D4583B", size=14, family="Arial", weight="bold"),
            offsetgroup=0
        ))

        fig1.add_trace(go.Scatter(
            x=filtered.index,
            y=filtered.values,
            name="Median Rent (€/m²)",
            mode="lines+markers",
            line=dict(color="black", width=2.5),
            marker=dict(size=8, color="black"),
            yaxis="y2"
        ))

        # Annotations
        fig1.add_annotation(
            x=filtered.index[0],
            y=-1,
            text=f"{filtered.iloc[0]:.2f} €/m²",
            showarrow=False,
            xanchor="left",
            yanchor="top",
            xshift=10,
            yshift=-10,
            bgcolor="black",
            font=dict(color="white", size=16),
            borderpad=4
        )

        fig1.add_annotation(
            x=filtered.index[-1],
            y=filtered.iloc[-1],
            text=f"{filtered.iloc[-1]:.2f} €/m²",
            showarrow=False,
            xanchor="right",
            yanchor="middle",
            bgcolor="black",
            font=dict(color="white", size=16),
            borderpad=4
        )
        fig1.add_shape(
            type="line",
            x0=2012.6, x1=2023.6,
            y0=0, y1=0,
            xref="x", yref="y",
            line=dict(color="black", width=1.5),
            layer="above"
        )
        # Layout
        fig1.update_layout(
            xaxis=dict(
                tickmode="linear", dtick=1,
                tickfont=dict(size=14, color="black"),
                showgrid=False, showline=True,
                linecolor="black", linewidth=1
            ),
            yaxis=dict(
                title=dict(text="Yearly Increase (%)", font=dict(color="black")),
                tickfont=dict(color="black"),
                showgrid=False, showline=True,
                linecolor="black", linewidth=1
            ),
            yaxis2=dict(
                title=dict(text="Median Rent (€/m²)", font=dict(color="black")),
                tickfont=dict(color="black"),
                overlaying="y", side="right",
                showgrid=False, showline=True,
                linecolor="black", linewidth=1
            ),
            plot_bgcolor="#ffffff",
            paper_bgcolor="#ffffff",
            legend=dict(x=0.01, y=0.99, font=dict(size=15)),
            showlegend=True,
            bargap=0.3,
            height=600,
            margin=dict(l=60, r=60, t=40, b=40),
            title=""
        )

        st.plotly_chart(fig1, use_container_width=True)

    st.markdown("---")

    COL1, COL2 = st.columns([2,5])

    with COL1:
        st.markdown("## Rent increases of 100% or more occurred in 129 PLRs, but the pattern is far from uniform.")

        rents_2013 = rents_PLR[rents_PLR["year"] == 2013][["plr_id", "median"]].rename(columns={"median": "rent_2013"})
        rents_2023 = rents_PLR[rents_PLR["year"] == 2023][["plr_id", "median"]].rename(columns={"median": "rent_2023"})

        rents_change = pd.merge(rents_2013, rents_2023, on="plr_id", how="inner")
        rents_change["pct_increase"] = ((rents_change["rent_2023"] - rents_change["rent_2013"]) / rents_change["rent_2013"]) * 100

        plr_geo["plr_id"] = plr_geo["plr_id"].astype(int)
        rents_change["plr_id"] = rents_change["plr_id"].astype(int)
        gdf_rents_change = plr_geo.merge(rents_change, on="plr_id", how="left")

        if "plr_name_x" in gdf_rents_change.columns:
            gdf_rents_change = gdf_rents_change.rename(columns={"plr_name_x": "plr_name"})
        elif "plr_name_y" in gdf_rents_change.columns:
            gdf_rents_change = gdf_rents_change.rename(columns={"plr_name_y": "plr_name"})

        geojson_rents_change = json.loads(gdf_rents_change.to_json())

        # Diverging scale: greys for negatives, red-orange for positives
        custom_diverging_scale = [
            [0.00, "#AAAAAA"],   # -40%
            [0.05, "#CCCCCC"],   # approx -20%
            [0.09, "#EEEEEE"],   # 0%
            [0.25, "#FFE3A7"],   # mid increase
            [0.50, "#FC9E5A"],   # higher
            [0.75, "#F03B20"],   # very high
            [1.00, "#BD0026"]    # 287%
        ]

        zmin = -40
        zmax = 300

        rents_change_named = rents_change.merge(plr_geo[["plr_id", "plr_name"]], on="plr_id", how="left")
        max_plr = rents_change_named.loc[rents_change_named["pct_increase"].idxmax()]
        min_plr = rents_change_named.loc[rents_change_named["pct_increase"].idxmin()]

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
                <div style="font-size:16px; font-weight:400; margin-bottom:4px;">Highest Rent Increase</div>
                <div style="font-size:36px; font-weight:500; color:black;">{max_plr['pct_increase']:.1f}%</div>
                <div style="font-size:16px; font-weight:600; color:black;">{max_plr['plr_name']}</div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
                <div style="font-size:16px; font-weight:400; margin-bottom:4px;">Lowest Rent Increase</div>
                <div style="font-size:36px; font-weight:500; color:black;">{min_plr['pct_increase']:.1f}%</div>
                <div style="font-size:16px; font-weight:600; color:black;">{min_plr['plr_name']}</div>
            """, unsafe_allow_html=True)

    with COL2:
        st.markdown("###### Median Rent Price Increases per PLR (2013–2023)")

        fig_rent_increase = px.choropleth_mapbox(
            gdf_rents_change,
            geojson=geojson_rents_change,
            locations="plr_id",
            featureidkey="properties.plr_id",
            color="pct_increase",
            color_continuous_scale=custom_diverging_scale,
            range_color=(zmin, zmax),
            mapbox_style="carto-positron",
            zoom=9.7,
            center={"lat": 52.52, "lon": 13.405},
            opacity=0.8,
            hover_name="plr_name",
            hover_data={
                "plr_id": False,
                "rent_2013": ':.2f',
                "rent_2023": ':.2f',
                "pct_increase": ':.1f'
            },
            labels={
                "plr_name": "PLR Name",
                "rent_2013": "Rent 2013 (€/m²)",
                "rent_2023": "Rent 2023 (€/m²)",
                "pct_increase": "Increase (%)"
            }
        )

        fig_rent_increase.update_layout(
            coloraxis_colorbar=dict(
                title="Rent Change (%)",
                orientation="v",
                x=0.99,
                y=0.5,
                xanchor="right",
                yanchor="middle",
                len=0.75,
                thickness=12,
                tickvals=[-40, 0, 50, 100, 200, 287],
                ticktext=["-40%", "0%", "50%", "100%", "200%", "287%"],
                title_font=dict(size=16, color="black"),
                tickfont=dict(size=14, color="black")
            ),
            margin=dict(t=0, b=0, l=0, r=0),
            height=800
        )

        fig_rent_increase.update_traces(
            marker_line_color="gray",
            marker_line_width=0.5,
            hoverlabel=dict(font_size=16, font_family="Arial", font_color="black")
        )

        st.plotly_chart(fig_rent_increase, use_container_width=True)

    st.markdown("---")

    st.markdown("## All districts saw rent increases of over 60% since 2013, while the share of high-end listings has surged to 31% citywide.")

    col1, col2 = st.columns([1,1])

    with col1:
        st.markdown("###### Median Rent Price Increases per District 2013 vs 2023")

        # Data prep
        rents_filtered = rents_BEZ[rents_BEZ["year"].isin([2013, 2023])].copy()
        rents_filtered["year"] = rents_filtered["year"].astype(str)

        pivot_df = rents_filtered.pivot(index="bez_name", columns="year", values="median").reset_index()
        pivot_df["pct_increase"] = ((pivot_df["2023"] - pivot_df["2013"]) / pivot_df["2013"] * 100).round(1)
        pivot_df["label"] = pivot_df["pct_increase"].astype(str) + "% increase"
        pivot_df = pivot_df.sort_values("2023", ascending=False)

        # Create figure
        fig3 = go.Figure()

        # Bar: 2013
        fig3.add_trace(go.Bar(
            y=pivot_df["bez_name"],
            x=pivot_df["2013"],
            name="2013",
            marker_color="lightgrey",
            orientation="h",
        ))

        # Bar: 2023 with annotations (and cliponaxis fix)
        fig3.add_trace(go.Bar(
            y=pivot_df["bez_name"],
            x=pivot_df["2023"],
            name="2023",
            marker_color="#D4583B",
            orientation="h",
            text=pivot_df["label"],
            textposition="outside",
            cliponaxis=False,
            insidetextanchor="start",
            textfont=dict(color="#D4583B", size=13, family="Arial", weight="bold")
        ))

        # Layout
        fig3.update_layout(
            yaxis=dict(
                title=None,
                tickfont=dict(size=16, color="black"),
                showgrid=False,
                showline=True,
                linecolor="black",
                linewidth=1,
                autorange="reversed"
            ),
            xaxis=dict(
                title="Median Rent (€/m²)",
                tickfont=dict(color="black"),
                showgrid=False,
                zeroline=False,
                showline=True,
                linecolor="black",
                linewidth=1,
                range=[0, max(pivot_df["2023"]) * 1.2],
                fixedrange=True
            ),

            barmode="group",
            bargap=0.4,
            plot_bgcolor="#ffffff",
            paper_bgcolor="#ffffff",
            legend=dict(
                x=1.0,
                y=0,
                xanchor="right",
                yanchor="bottom",
                orientation="v",
                font=dict(size=16, color="black")
            ),
            height=800,
            margin=dict(l=120, r=120, t=30, b=40),
            title="")

        fig3.update_traces(
            hoverlabel=dict(
                font_size=16,
                font_family="Arial",
                font_color="black")
        )

        st.plotly_chart(fig3, use_container_width=True)

    with col2:
        st.markdown("###### Rental Market Segmentation 2023")

        # 1. Copy and rename Berlin insgesamt
        rent_structure_fixed = rent_structure.copy()
        rent_structure_fixed.loc[rent_structure_fixed["Bezirk"] == "Berlin insgesamt", "Bezirk"] = "Total Berlin"

        # 2. Separate and sort all but "Total Berlin"
        df_main = rent_structure_fixed[rent_structure_fixed["Bezirk"] != "Total Berlin"]
        df_total = rent_structure_fixed[rent_structure_fixed["Bezirk"] == "Total Berlin"]

        # 3. Sort by most expensive, then append "Total Berlin"
        df_sorted = pd.concat([
            df_main.sort_values(by="≥18 EUR/m²", ascending=False),
            df_total
        ], ignore_index=True)

        # 4. Get the column order and reverse for expensive → affordable
        price_columns_structure = [col for col in rent_structure.columns if col != "Bezirk"]
        reversed_columns = list(reversed(price_columns_structure))

        # 5. Reverse the color scale too
        orange_gradient_structure = [
            "#D4583B", "#D94425", "#ED4F2D", "#F86A3C", "#FC8C5C", "#FDB99B", "#FEE2D5"]

        # 6. Prepare manual y-axis category order
        district_order = df_sorted["Bezirk"].tolist()
        # Reverse the order of districts, keeping "Total Berlin" at the end
        district_order = district_order[:-1][::-1] + [district_order[-1]]

        # 7. Create chart with conditional annotations
        fig_rent_structure_chart = go.Figure()
        x_offsets = {bez: 0 for bez in df_sorted["Bezirk"]}

        for i, col in enumerate(reversed_columns):
            x_values = []
            texts = []

            for idx, row in df_sorted.iterrows():
                bez = row["Bezirk"]
                current_value = row[col]
                offset = x_offsets[bez]

                if bez == "Total Berlin":
                    x_values.append(current_value / 2 + offset)
                    texts.append(f"{current_value}%")
                else:
                    x_values.append(None)
                    texts.append("")

                # Update offset for next segment
                x_offsets[bez] += current_value

            fig_rent_structure_chart.add_trace(go.Bar(
                y=df_sorted["Bezirk"],
                x=df_sorted[col],
                name=col,
                orientation="h",
                marker=dict(color=orange_gradient_structure[i]),
                text=texts,
                textposition="none",
                textfont=dict(color="white", size=12, family="Arial", weight="bold"),
                customdata=x_values,
                hovertemplate=f"{col}: %{{x}}<extra></extra>"
            ))

        # 8. Layout
        fig_rent_structure_chart.update_layout(
            barmode="stack",
            xaxis=dict(
                title="Share of Listings (%)",
                ticksuffix="%",
                tickfont=dict(size=16, color="black"),
                range=[0, 100],
                showline=True,
                linecolor="black",
                linewidth=1,
            ),
            yaxis=dict(
                title=None,
                type="category",
                categoryorder="array",
                categoryarray=district_order,
                showline=True,
                linecolor="black",
                linewidth=1,
                tickfont=dict(size=16, color="black"),
            ),
            plot_bgcolor="#ffffff",
            paper_bgcolor="#ffffff",
            height=800,
            margin=dict(l=140, r=40, t=30, b=40),
            legend=dict(
                title="Monthly Cold Rent",
                title_font=dict(size=14, color="black", weight="bold"),
                font=dict(size=14, color="black"),
                traceorder="normal",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02
            ),
            title=""
        )
        for trace in fig_rent_structure_chart.data:
            for i, (x, y, text) in enumerate(zip(trace.customdata, trace.y, trace.text)):
                if x is not None and text:
                    fig_rent_structure_chart.add_annotation(
                        x=x,
                        y=y,
                        text=text,
                        showarrow=False,
                        font=dict(color="white", size=14, family="Arial", weight="bold"),
                        xanchor="center",
                        yanchor="middle"
                    )
        fig_rent_structure_chart.update_traces(
            hoverlabel=dict(
                font_size=16,
                font_family="Arial",
                font_color="black"
            )
        )

        st.plotly_chart(fig_rent_structure_chart, use_container_width=True)

    st.markdown("---")
