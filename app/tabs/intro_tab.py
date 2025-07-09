import pandas as pd
import geopandas as gpd
import streamlit as st
import json
import plotly.express as px
from data_loader import load_rents_PLR, load_plr_geo
from data_loader import IMAGES_DIR
import os

rents_PLR = load_rents_PLR()
plr_geo = load_plr_geo()

def show_intro_tab():
    st.markdown("# Affordable for Whom?")
    st.markdown("##### Exploring Rental Affordability in Berlin (2013–2023)")

    col1, spacer, col2 = st.columns([18,1,5])
    with col1:
        # Merge rents data with geometry
        rents_geometry_merged = rents_PLR.merge(plr_geo[["plr_id", "geometry"]], on="plr_id", how="left")
        gdf_rents_plr = gpd.GeoDataFrame(rents_geometry_merged, geometry="geometry", crs="EPSG:4326")

        # Filter for 2013–2023
        gdf_rents_filtered = gdf_rents_plr[(gdf_rents_plr["year"].between(2013, 2023)) & gdf_rents_plr["geometry"].notnull()].copy()

        # Create GeoJSON dictionary from unique geometries
        geojson_rents_plr = json.loads(
            gdf_rents_filtered.drop_duplicates("plr_id")[["plr_id", "geometry"]].to_json())

        # Define color range
        vmin = gdf_rents_filtered["median"].min()
        vmax = gdf_rents_filtered["median"].max()

        # Build animated choropleth map
        fig_rent_choropleth = px.choropleth_mapbox(
            gdf_rents_filtered.sort_values("year"),
            geojson=geojson_rents_plr,
            locations="plr_id",
            featureidkey="properties.plr_id",
            color="median",
            hover_name="plr_name",
            hover_data={"plr_id": False},
            animation_frame="year",
            color_continuous_scale="YlOrRd",
            range_color=(vmin, vmax),
            mapbox_style="carto-positron",
            zoom=9.7,
            center={"lat": 52.49, "lon": 13.405},
            opacity=0.7,
            labels={"median": "Median Rent (€/m²)", "year": "Year "},
        )

        # Layout and border styling
        fig_rent_choropleth.update_layout(
            height=800,
            title="",
            margin=dict(r=0, t=0, l=0, b=0),
            coloraxis_colorbar=dict(
                title="Median<br>Rent (€/m²)",
                title_font=dict(size=16, color="black", weight="bold"),
                tickfont=dict(size=14, color="black"),
                x=0.997,
                xanchor="right",
                y=0.55,
                yanchor="middle",
                len=0.85
            )
        )

        fig_rent_choropleth.update_layout(
            updatemenus=[{
                "type": "buttons",
                "buttons": [{
                    "label": "Play",
                    "method": "animate",
                    "args": [None, {
                        "frame": {"duration": 1500, "redraw": True},
                        "fromcurrent": True,
                        "transition": {"duration": 500},
                        "mode": "immediate"
                    }]
                }, {
                    "label": "Pause",
                    "method": "animate",
                    "args": [[None], {
                        "frame": {"duration": 0, "redraw": False},
                        "mode": "immediate"
                    }]
                }],
                    "font": {"size": 14, "color": "black"},
                    "x": 0.1,
                    "y": 0.2,
                    "direction": "left"
                }],
            sliders=[{
                "active": 0,
                "font": {"size": 16, "color": "black"},
                "currentvalue": {
                    "prefix": "Year ",
                    "visible": True,
                    "font": {"size": 16, "color": "black", "family": "Arial Black"}
                },
                "steps": [{
                    "label": str(year),
                    "method": "animate",
                    "args": [[str(year)], {
                        "frame": {"duration": 0, "redraw": True},
                        "mode": "immediate"
                    }]
                } for year in sorted(gdf_rents_filtered["year"].unique())],
                "x": 0.11,
                "y": 0.22,
                "len": 0.85
            }]
        )
        
        fig_rent_choropleth.update_traces(
            marker_line_color="gray",
            marker_line_width=0.5,
            hoverlabel=dict(font_size=16,font_family="Arial", font_color="black")
        )
        st.plotly_chart(fig_rent_choropleth, use_container_width=True)

    with col2:
        st.markdown("###### Berlin has changed. But who has been priced out?")
        st.markdown("This project looks at how rent prices, income, and housing dynamics have reshaped access to housing in Berlin — and who can still afford to live here.")
        st.markdown("Over the past decade, rising rents have outpaced income growth for many, making large parts of the city increasingly unaffordable, especially for low-income residents.", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<div style='margin-top:220px'></div>", unsafe_allow_html=True)
    st.markdown("##### The city that built its reputation on cheap living and open culture is becoming increasingly inaccessible. But...")
    st.markdown("<div style='margin-top:80px'></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        with st.expander("1", expanded=True):
            st.markdown("<div style='margin-top:100px'></div>", unsafe_allow_html=True)
            st.markdown("""### <span style='display: inline-flex; align-items: center; justify-content: center; width: 40px; height: 40px; border-radius: 50%; background: #D4583B; color: white; font-weight: bold; margin-right: 10px; font-size: 20px;'>1</span> """, unsafe_allow_html=True)
            st.markdown("## Who is actually being priced out?")
            st.markdown("<div style='margin-top:120px'></div>", unsafe_allow_html=True)
    with col2:
        with st.expander("2", expanded=True):
            st.markdown("<div style='margin-top:98.5px'></div>", unsafe_allow_html=True)
            st.markdown("""## <span style='display: inline-flex; align-items: center; justify-content: center; width: 40px; height: 40px; border-radius: 50%; background: #D4583B; color: white; font-weight: bold; margin-right: 10px; font-size: 20px;'>2</span> """, unsafe_allow_html=True)
            st.markdown("## What does affordable even mean in this context?")
            st.markdown("<div style='margin-top:98.5px'></div>", unsafe_allow_html=True)
    with col3:
        with st.expander("3", expanded=True):
            st.markdown("<div style='margin-top:79px'></div>", unsafe_allow_html=True)
            st.markdown("""## <span style='display: inline-flex; align-items: center; justify-content: center; width: 40px; height: 40px; border-radius: 50%; background: #D4583B; color: white; font-weight: bold; margin-right: 10px; font-size: 20px;'>3</span> """, unsafe_allow_html=True)
            st.markdown("## How does rent affordability compare across the city and by income?")
            st.markdown("<div style='margin-top:79px'></div>", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:300px'></div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Framework and Definitions")
    st.markdown("<div style='margin-top:40px'></div>", unsafe_allow_html=True)

    with st.expander("Housing Affordability", expanded=True):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            st.markdown("### What is Housing Affordability?")
        with col2:
            st.markdown("""
            Housing is considered **affordable** if a household spends no more than **30% of its net income** on rent.  
            Rent burden above this threshold is considered financially straining — especially for low-income households.
            """)
            st.markdown("<div style='margin-top:px'></div>", unsafe_allow_html=True)
        with col3:
            st.markdown("<div style='margin-top:40px'></div>", unsafe_allow_html=True)
            st.latex(r"\text{Rent Burden} = \frac{\text{Monthly Rent}}{\text{Net Income}}")
            st.markdown("<div style='margin-top:40px'></div>", unsafe_allow_html=True)

    with st.expander("LOR", expanded=True):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            st.markdown("### What are LOR?")
        with col2:
            st.markdown("""
            The Lebensweltlich Orientierte Räume system divides the city into standardized spatial units to support neighborhood-level analysis and policy-making based on social and everyday life structures.
            As of the 2021 update, Berlin is divided into:
            - **12** Bezirke (districts)
            - **52** Prognoseräume (PGRs) — upper-level forecasting areas
            - **143** Bezirksräume (BZRs) — medium-level forecasting areas
            - **542** Planungsräume (PLRs) — the smallest, most granular unit in this analysis 
            """)
        with col3:
            image_path_LOR = os.path.join(IMAGES_DIR, "LOR.png")
            st.image(image_path_LOR)
    with st.expander("Rent Definitions", expanded=True):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            st.markdown("### What kind of Rent is analyzed?")
        with col2:
            st.markdown("""
            This project uses **cold rent (Kaltmiete)** from **new listings**, reflecting market entry prices between 2013 and 2023.  
            These prices are not the same as the **Mietspiegel**, which represents average rents across existing contracts.  
            Warm rent (*Warmmiete*), which includes heating and service charges, is not analyzed here.
            """)
        with col3:
            st.markdown("""
            Apartments are grouped by number of rooms:
            - **1-room**: up to 50 m²  
            - **2-room**: ~50–65 m²  
            - **3 rooms**: over 80 m²  

            Most affordability comparisons focus on **1-room apartments**, as they are typically the most accessible for low-income residents.
            """)

    with st.expander("Rent-Controlled & Regulated Units", expanded=True):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            st.markdown("### What is Subsidized Housing?")
        with col2:
            st.markdown("""
            Subsidized housing includes units with **rent or access restrictions**, often tied to public funding.  
            Tenants typically need a **WBS certificate** *(Wohnungsberechtigungsschein)* to qualify.  
            These units can be owned by either **public** or **private** landlords.
            """)
        with col3:
            image_path_subsidized = os.path.join(IMAGES_DIR, "subsidized_housing.png")
            st.image(image_path_subsidized)

    with st.expander("Income Definitions", expanded=True):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            st.markdown("###  What Income is used?")
        with col2:
            st.markdown("""
            This project uses **monthly net income per inhabitant** *(Verfügbares Einkommen der privaten Haushalte je Einwohner)*  
            It compares:
            - **Median net income**
            - **Bürgergeld** allowance and maximum coverage for rent. 

            These values are used to estimate **rent burden** and assess affordability across groups.
            """)
        with col3:
            st.markdown("")

    st.markdown("---")

    col1, col2 = st.columns([1,3])

    with col1:
        st.markdown("<div style='margin-top:40px'></div>", unsafe_allow_html=True)
        st.markdown("### Data Sources")
        st.markdown("<div style='margin-top:40px'></div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div style='margin-top:40px'></div>", unsafe_allow_html=True)
        st.markdown("""
        <style>
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 1em;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 0.8em;
            vertical-align: top;
        }
        th {
            background-color: #f6f6f6;
            text-align: left;
        }
        td {
            background-color: #ffffff;
        }
        strong {
            font-weight: 600;
        }
        </style>

        <table>
        <thead>
        <tr>
            <th>Source</th>
            <th>Description</th>
        </tr>
        </thead>
        <tbody>
        <tr>
            <td>Amt für Statistik Berlin-Brandenburg (<strong>AfS</strong>)</td>
            <td>Population by PLR, Income 2022–2024, Household data 2023</td>
        </tr>
        <tr>
            <td>Investitions Bank Berlin Housing Market Reports (<strong>IBB</strong>)</td>
            <td>Median and Average Rent prices by PLR 2013–2014, Rent Trends</td>
        </tr>
        <tr>
            <td>Bundesagentur für Arbeit (<strong>AfA</strong>)</td>
            <td>Unemployment rates, Bürgergeld caps</td>
        </tr>
        <tr>
            <td><strong>Wohnatlas 2022</strong>, Senatsverwaltung für Stadtentwicklung, Bauen und Wohnen (<strong>SenStadt</strong>)</td>
            <td>Social housing %, Social Welfare Recipients %, Geographic Information</td>
        </tr>
        <tr>
            <td>Verband Berlin-Brandenburgischer Wohnungsunternehmen (<strong>BBU</strong>)</td>
            <td>Social Housing data for 2017–2023</td>
        </tr>
        </tbody>
        </table>
        """, unsafe_allow_html=True)
        st.markdown("<div style='margin-top:40px'></div>", unsafe_allow_html=True)

    st.markdown("---")

    col1, col2 = st.columns([1,3])
    with col1:
        st.markdown("<div style='margin-top:40px'></div>", unsafe_allow_html=True)
        st.markdown("### Tech Stack")
        st.markdown("<div style='margin-top:40px'></div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div style='margin-top:40px'></div>", unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns([1,1,1,1])
        with col1:
            image_path_python = os.path.join(IMAGES_DIR, "python.svg")
            st.image(image_path_python)
        with col2:
            image_path_pandas = os.path.join(IMAGES_DIR, "pandas.svg")
            st.image(image_path_pandas)
        with col3:
            image_path_tableau = os.path.join(IMAGES_DIR, "tableau.svg")
            st.image(image_path_tableau)            
        with col4:
            image_path_plotly = os.path.join(IMAGES_DIR, "plotly.svg")
            st.image(image_path_plotly)             

        st.markdown("<div style='margin-top:40px'></div>", unsafe_allow_html=True)
    st.markdown("---")