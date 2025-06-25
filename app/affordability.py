import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import geopandas as gpd
import json
import plotly.express as px
import plotly.graph_objects as go

rents_BEZ = pd.read_csv('../data/csv/rent/rents_BEZ.csv') # 2012 - 2024
rents_PLR = pd.read_csv('../data/csv/rent/rents_PLR.csv') # 2   012 - 2024
rent_structure= pd.read_csv('../data/csv/rent/rent_price_structure_2023.csv')

pop_BEZ = pd.read_csv('../data/csv/population/population_BEZ.csv') # 2012 - 2024
net_migration = pd.read_csv('../data/csv/population/net_migration_BEZ.csv') # 2014 - 2023

subsidies = pd.read_csv('../data/csv/public_housing/social_housing_subsidized_berlin.csv') # 2015 - 2024
sh_total = pd.read_csv('../data/csv/public_housing/sh_total_units.csv', sep=";") # 2017 - 2023
sh_total_new = pd.read_csv('../data/csv/public_housing/sh_total_new.csv') # 2017 - 2023
sh_subsidized_totals = pd.read_csv('../data/csv/public_housing/sh_subsidized_totals.csv') # 2017 - 2023
wbs_berlin = pd.read_csv('../data/csv/public_housing/wbs_berlin.csv') # 2015 - 2024

income_households_berlin = pd.read_csv('../data/csv/income/income_household_13_23.csv') # 2013 - 2023
income_persons_berlin = pd.read_csv('../data/csv/income/disposable_income.csv') # 1991 - 2023

wohnatlas_2022 = pd.read_csv('../data/csv/wohnatlas/wohnatlas_2022.csv') # (2017) - 2022

households = pd.read_csv('../data/csv/general_housing/households_berlin.csv') # 2013 - 2023
housing_totals_BEZ = pd.read_csv('../data/csv/general_housing/housing_units_BEZ.csv') # 2013 - 2023

plr_geo = gpd.read_file("../data/geo/2021_PLR.geojson")
plr_geo = plr_geo.to_crs(epsg=4326)
plr_geo = plr_geo.rename(columns={
    "PLR_ID": "plr_id",
    "PLR_NAME": "plr_name",
    "BEZ": "bez_id"
})
plr_geo["plr_id"] = plr_geo["plr_id"].astype(int)
plr_geo["bez_id"] = plr_geo["bez_id"].astype(int)

pgr_geo = gpd.read_file("../data/geo/2021_PGR.geojson")
pgr_geo = pgr_geo.to_crs(epsg=4326)
pgr_geo = pgr_geo.rename(columns={
    "PGR_ID": "pgr_id",
    "PGR_NAME": "pgr_name",
    "BEZ": "bez_id"
})
pgr_geo["pgr_id"] = pgr_geo["pgr_id"].astype(int)
pgr_geo["bez_id"] = pgr_geo["bez_id"].astype(int)

st.set_page_config(layout="wide")

# ---- GLOBAL CSS ----
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;700&display=swap');

    html, body, .stApp {
        font-family: 'Inter', sans-serif !important;
        color: #222;
        background-color: #f7f7f7;
    }

    .stMarkdown h1 {
        font-size: 2.4rem;
        font-weight: 600;
    }

    .stMarkdown h2 {
        font-size: 2rem;
        font-weight: 600;
    }

    .stMarkdown  h3 {
        font-size: 1.8rem;
        font-weight: 600;
    }

    .stMarkdown h4 {
        font-size: 2rem;
        font-weight: 500;
    }

    .stMarkdown h5 {
        font-size: 1.3rem;
        font-weight: 400;
    }

    .stMarkdown h6 {
        font-size: 1rem;
        font-weight: 600;
    }

    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {
        font-family: 'Inter', sans-serif !important;
        text-align: left;
    }

    .stMarkdown p, .stMarkdown ul, .stMarkdown ol, .stMarkdown li {
        font-size: 1rem;
        line-height: 1.8;
        font-family: 'Inter', sans-serif !important;
        text-align: left;
    }
            
    .caption {
        font-size: 0.8rem !important;
        font-style: italic;
        text-align: left;
        margin-top: 0.5rem;
    }
            
    .scroll-button {
        color: #D4583B !important;
        font-weight: 400;
        font-size: 1rem;
        border: 1px solid #ccc;
        border-radius: 8px;
        text-decoration: none;
        padding: 0.6rem 1.2rem;
        background-color: transparent;
        display: inline-block;
        margin-top: 1rem;
        cursor: pointer;
    }

    .scroll-button:hover {
        border-color: #D4583B;
        color: #b6462f;
    }

    .stTabs [role="tablist"] {
        border-bottom: 2px solid #ddd;
        position: sticky;
        top: 0px;
        background-color: #f7f7f7;
        z-index: 999;
        padding-top: 0px;
    }

    .stTabs [role="tab"] {
        font-family: 'Inter', sans-serif !important;
        font-size: 22px;
        font-weight: 500;
        color: #444;
        background-color: #f7f7f7;
        padding: 12px 24px;
        margin-right: 2px;
        border: none;
        border-top-left-radius: 5px;
        border-top-right-radius: 5px;
        transition: background-color 0.2s ease;
    }

    .stTabs [aria-selected="true"] {
        background-color: #eaeaea;
        font-weight: 700;
        color: #111;
        border-bottom: 2px solid transparent;
    }

    .stTabs [role="tab"]:hover {
        background-color: #ebebeb;
        color: #000;
    }
            
    details > summary span.css-10trblm {
        font-size: 2rem !important;
        font-weight: 600 !important;
    }
            
    header[data-testid="stHeader"] {
        background: transparent !important;
        height: 0rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# ---- TABS ----
tabs = st.tabs(["Introduction", "Supply", "Demand", "Affordability", "Social Housing", "Outlook"])

# ---- TAB STRUCTURE ----
with tabs[0]:
    st.markdown("# Affordable for Whom?")
    st.markdown("##### Exploring Rental Affordability in Berlin (2013–2023)")

    col1, spacer, col2 = st.columns([18,1,5])
    with col1:
        # 1. Merge rents data with geometry
        rents_geometry_merged = rents_PLR.merge(plr_geo[["plr_id", "geometry"]], on="plr_id", how="left")
        gdf_rents_plr = gpd.GeoDataFrame(rents_geometry_merged, geometry="geometry", crs="EPSG:4326")

        # 2. Filter for 2013–2023 and cast plr_id to string
        gdf_rents_filtered = gdf_rents_plr[(gdf_rents_plr["year"].between(2013, 2023)) & gdf_rents_plr["geometry"].notnull()].copy()
        gdf_rents_filtered["plr_id"] = gdf_rents_filtered["plr_id"].astype(str)

        # 3. Create GeoJSON dictionary from unique geometries
        geojson_rents_plr = json.loads(
            gdf_rents_filtered.drop_duplicates("plr_id")[["plr_id", "geometry"]].to_json())

        # 4. Define color range
        vmin = gdf_rents_filtered["median"].min()
        vmax = gdf_rents_filtered["median"].max()

        # 5. Build animated choropleth map
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

        # 6. Layout and border styling
        fig_rent_choropleth.update_layout(
            height=800,
            title="",
            margin=dict(r=0, t=0, l=0, b=0),
            coloraxis_colorbar=dict(
                title="Median<br>Rent (€/m²)",
                title_font=dict(size=16, color="black"),
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
        with st.expander("1", expanded=False):
            st.markdown("<div style='margin-top:100px'></div>", unsafe_allow_html=True)
            st.markdown("""### <span style='display: inline-flex; align-items: center; justify-content: center; width: 40px; height: 40px; border-radius: 50%; background: #D4583B; color: white; font-weight: bold; margin-right: 10px; font-size: 20px;'>1</span> """, unsafe_allow_html=True)
            st.markdown("## Who is actually being priced out?")
            st.markdown("<div style='margin-top:100px'></div>", unsafe_allow_html=True)
    with col2:
        with st.expander("2", expanded=False):
            st.markdown("<div style='margin-top:98.5px'></div>", unsafe_allow_html=True)
            st.markdown("""## <span style='display: inline-flex; align-items: center; justify-content: center; width: 40px; height: 40px; border-radius: 50%; background: #D4583B; color: white; font-weight: bold; margin-right: 10px; font-size: 20px;'>2</span> """, unsafe_allow_html=True)
            st.markdown("## What does affordable even mean in this context?")
            st.markdown("<div style='margin-top:98.5px'></div>", unsafe_allow_html=True)
    with col3:
        with st.expander("3", expanded=False):
            st.markdown("<div style='margin-top:79px'></div>", unsafe_allow_html=True)
            st.markdown("""## <span style='display: inline-flex; align-items: center; justify-content: center; width: 40px; height: 40px; border-radius: 50%; background: #D4583B; color: white; font-weight: bold; margin-right: 10px; font-size: 20px;'>3</span> """, unsafe_allow_html=True)
            st.markdown("## How does rent affordability compare across the city and by income?")
            st.markdown("<div style='margin-top:79px'></div>", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:300px'></div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Framework and Definitions")

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
            st.image("./LOR.png")

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
            st.image("./subsidized_housing.png")

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
        st.markdown("### Data Sources")
    with col2:
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
    
    st.markdown("---")

    col1, col2 = st.columns([1,3])
    with col1:
        st.markdown("### Tech Stack")
    with col2:
        col1, col2, col3, col4 = st.columns([1,1,1,1])
        with col1:
            st.image("./python.svg")
        with col2:
            st.image("./pandas.svg")
        with col3:
            st.image("./tableau.svg")
        with col4:
            st.image("./plotly.svg")

    st.markdown("---")

with tabs[1]:
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
            [0.09, "#EEEEEE"], # 0%
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

with tabs[2]:
    st.markdown("## Population Dynamics and Income Trends")
    st.markdown("---")

    col1, col2 = st.columns([2,5])
    
    with col1:
        st.markdown("## The population grew by 315,934 representing an 8,87%.")
        st.markdown("<div style='margin-top:40px'></div>", unsafe_allow_html=True)
        st.markdown('<p class="caption">* Based on residents registered through the population registration system.</p>', unsafe_allow_html=True)
        st.markdown('<p class="caption">* In Reinickendorf and Tempelhof-Schöneberg, special effects are present due to initial reception centers for asylum seekers.</p>', unsafe_allow_html=True)

    with col2:
        st.markdown("###### Population Growth and Net Migration")
        # Clean Bezirke list and rename "Berlin Insgesamt"
        pop_BEZ["bez_name"] = pop_BEZ["bez_name"].str.strip()
        net_migration["bez_name"] = net_migration["bez_name"].str.strip()
        bez_options_pop = sorted(net_migration["bez_name"].replace({"Berlin Insgesamt": "All Berlin"}).unique().tolist())

        # Dropdown menu
        selected_bezirk_pop = st.selectbox("Choose a district", options=bez_options_pop, key="selectbox_pop")

        # Revert label for filtering
        filter_bezirk = "Berlin Insgesamt" if selected_bezirk_pop == "All Berlin" else selected_bezirk_pop

        # Prepare filtered data
        if selected_bezirk_pop == "All Berlin":
            pop_filtered = pop_BEZ.groupby("year")["population"].sum().reset_index()
            mig_filtered = (
                net_migration[net_migration["bez_name"] != "Berlin Insgesamt"]
                .groupby("year")["net_migration"]
                .sum()
                .reset_index()
            )
        else:
            pop_filtered = pop_BEZ[pop_BEZ["bez_name"] == filter_bezirk][["year", "population"]].copy()
            mig_filtered = net_migration[net_migration["bez_name"] == filter_bezirk][["year", "net_migration"]].copy()

        # Merge and sort
        growth_df = pd.merge(pop_filtered, mig_filtered, on="year", how="inner").sort_values("year")

        # Build figure
        fig_berlin_pop_migration = go.Figure()

        fig_berlin_pop_migration.add_trace(go.Scatter(
            x=growth_df["year"],
            y=growth_df["population"],
            name="Total Population",
            mode="lines+markers",
            line=dict(color="black", width=2),
            marker=dict(size=8, color="black"),
            yaxis="y1",
            hovertemplate="Total Population: %{y:,}<extra></extra>"
        ))

        fig_berlin_pop_migration.add_trace(go.Bar(
            x=growth_df["year"],
            y=growth_df["net_migration"],
            base=0,
            name="Net Migration",
            marker_color="#D4583B",
            yaxis="y2",
            width=0.5,
            text=[f"{v:,}" for v in growth_df["net_migration"]],
            textposition="outside",
            textfont=dict(color="#D4583B", size=13, family="Arial Black"),
            hovertemplate="Net Migration: %{y:,}<extra></extra>"
        ))

        # Annotate first and last points
        if not growth_df.empty:
        # Always annotate the first point
            fig_berlin_pop_migration.add_annotation(
                x=growth_df["year"].iloc[0],
                y=growth_df["population"].iloc[0] * 0.98,
                text=f"{growth_df['population'].iloc[0]:,}",
                showarrow=False,
                xanchor="center",
                yanchor="top",
                font=dict(color="white", size=16),
                bgcolor="black",
                borderpad=4
            )

        # Annotate last point only if there's more than one
        if len(growth_df) > 1:
            fig_berlin_pop_migration.add_annotation(
                x=growth_df["year"].iloc[-1],
                y=growth_df["population"].iloc[-1] * 0.98,
                text=f"{growth_df['population'].iloc[-1]:,}",
                showarrow=False,
                xanchor="center",
                yanchor="top",
                font=dict(color="white", size=16),
                bgcolor="black",
                borderpad=4
            )

        # 0-line
        fig_berlin_pop_migration.add_shape(
            type="line",
            xref="paper",
            yref="y2",
            x0=0, x1=1,
            y0=0, y1=0,
            line=dict(color="black", width=2)
        )

        # Layout styling
        fig_berlin_pop_migration.update_layout(
            height=600,
            plot_bgcolor="white",
            paper_bgcolor="white",
            bargap=0,
            xaxis=dict(
                title=None,
                tickmode="linear",
                dtick=1,
                tickfont=dict(size=16, color="black"),
                showline=True,
                ticks='outside',
                showgrid=False,
                linecolor="black",
                automargin=False,
                constrain="domain"
            ),
            yaxis=dict(
                title=dict(text="Total Population", font=dict(color="black")),
                tickfont=dict(size=16, color="black"),
                showline=True,
                showgrid=False,
                linecolor="black",
                rangemode="tozero",
                automargin=False,
                constrain="domain"
            ),
            yaxis2=dict(
                title=dict(text="Net Migration", font=dict(color="black")),
                tickfont=dict(size=16, color="black"),
                range=[0, 180000],
                overlaying="y",
                side="right",
                showline=True,
                showgrid=False,
                linecolor="black",
                automargin=False,
                constrain="domain"
            ),
            legend=dict(
                x=0.01, y=1.02,
                font=dict(size=16, color="black")
            ),
            margin=dict(l=80, r=80, t=40, b=40),
            hoverlabel=dict(font_size=16, font_family="Arial", font_color="black")
        )

        st.plotly_chart(fig_berlin_pop_migration, use_container_width=True)

    st.markdown("---")

    st.markdown("## While rent prices increased, so did incomes —<br>particularly among those in the middle and upper brackets.", unsafe_allow_html=True)
    st.markdown('<p class="caption">* The income increases are not adjusted to inflation.</p>', unsafe_allow_html=True)

    col1, col2 = st.columns([1,1])
    
    with col1:
        st.markdown("###### Average Net Household Income per Inhabitant since 1991 ")
        # Load and clean
        income_persons_berlin["monthly_disposable_income"] = (
            income_persons_berlin["monthly_disposable_income"]
            .astype(str)
            .str.replace(",", ".", regex=False)
            .astype(float))

        # Create chart
        fig_income_line = go.Figure()

        fig_income_line.add_trace(go.Scatter(
            x=income_persons_berlin["year"],
            y=income_persons_berlin["monthly_disposable_income"],
            mode="lines+markers",
            name="Monthly Net Income",
            line=dict(color="black", width=2),
            marker=dict(size=6, color="black"),
            hovertemplate="Year: %{x}<br>Income: %{y:.2f} €<extra></extra>"
        ))

        # Annotate last value
        last_year = income_persons_berlin["year"].iloc[-1]
        last_value = income_persons_berlin["monthly_disposable_income"].iloc[-1]

        fig_income_line.add_annotation(
            x=last_year,
            y=last_value,
            text=f"{last_value:.2f} €",
            showarrow=False,
            xanchor="center",
            yanchor="top",
            font=dict(color="white", size=16, weight="bold"),
            bgcolor="black",
            borderpad=4
        )

        # Layout styling
        fig_income_line.update_layout(
            height=600,
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(l=60, r=60, t=40, b=60),
            xaxis=dict(
                title=None,
                tickmode="linear",
                dtick=2,
                tickfont=dict(size=14, color="black"),
                showline=True,
                linecolor="black"
            ),
            yaxis=dict(
                title="Monthly Disposable Income (€)",
                tickfont=dict(color="black"),
                showline=True,
                rangemode="tozero",
                linecolor="black"
            ),
            legend=dict(
                x=0.01, y=0.99,
                font=dict(size=12, color="black")
            )
        )

        st.plotly_chart(fig_income_line, use_container_width=True)

    with col2:
        st.markdown("###### Income Brackets Evolution % (2013–2023)")
        income_cols = [
            "%_under_900",
            "%_900_1500",
            "%_1500_2600",
            "%_2600_4500",
            "%_over_4500"]

        # Convert percentages from comma to float
        for col in income_cols:
            income_households_berlin[col] = (
                income_households_berlin[col]
                .astype(str)
                .str.replace(",", ".", regex=False)
                .astype(float))

        orange_gradient_income = [
            "#FEE2D5", "#FDB99B", "#FC8C5C", "#F86A3C", "#D4583B"]

        fig_income_stack = go.Figure()

        for col, color in zip(income_cols, orange_gradient_income):
            label = col.replace("%_", "").replace("_", "–").replace("over", "Over ")
            fig_income_stack.add_trace(go.Scatter(
                x=income_households_berlin["year"],
                y=income_households_berlin[col],
                name=label,
                stackgroup="one",
                groupnorm="percent",
                mode="none",
                fillcolor=color,
                hovertemplate=f"{label}: %{{y:.2f}}%<extra></extra>"
            ))

        # Layout updates
        fig_income_stack.update_layout(
            height=600,
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(l=60, r=60, t=40, b=60),
            xaxis=dict(
                title=None,
                tickmode="linear",
                dtick=1,
                tickfont=dict(size=16, color="black"),
                showline=True,
                linecolor="black"
            ),
            yaxis=dict(
                title="Share of Households (%)",
                range=[0, 100],
                ticksuffix="%",
                showline=True,
                linecolor="black",
                tickfont=dict(size=16, color="black")
            ),
            legend=dict(
                title="Monthly<br>Net Income (€)",
                title_font=dict(size=16, color="black", weight="bold"),
                font=dict(size=16, color="black"),
                traceorder="normal",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.01
            ),
            hoverlabel=dict(
                font_size=16,
                font_family="Arial",
                font_color="black"
            )
        )

        # Add annotations for 2013 and 2023
        annotations = []
        years_to_annotate = [2013, 2023]

        for year in years_to_annotate:
            year_data = income_households_berlin[income_households_berlin["year"] == year]
            y_base = 0
            for col in income_cols:
                value = year_data[col].values[0]
                y_center = y_base + value / 2
                x_shift = 0.4 if year == 2013 else -0.4

                annotations.append(dict(
                    x=year + x_shift,
                    y=y_center,
                    text=f"{value:.1f}%",
                    showarrow=False,
                    font=dict(color="white", size=14, family="Arial"),
                    xanchor="center",
                    yanchor="middle"
                ))
                y_base += value

        fig_income_stack.update_layout(annotations=annotations)

        st.plotly_chart(fig_income_stack, use_container_width=True)

    st.markdown("---")

with tabs[3]:
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
        income_df = income_persons_berlin[income_persons_berlin["year"].between(2013, 2023)].copy()
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
        st.markdown("**Asummptions:**\n- Average median available income 2023: 2031€/month.\n- Size 1-room-apartment: 50m².")
      

    with col2:
        st.markdown("###### Rent Burden by PLR 2023 (Median Income Earner, 1R Apartment)")

        col1, col2 = st.columns([10, 1])
        
        with col1:
            # 1. Get median income for Berlin 2023
            income_2023 = income_households_berlin[income_households_berlin["year"] == 2023]["monthly_available_income"].values[0]

            # 2. Filter rent prices for 2023 and calculate 1R rent & rent burden
            rents_2023 = rents_PLR[rents_PLR["year"] == 2023][["plr_id", "median"]].copy()
            rents_2023["rent_1R"] = rents_2023["median"] * 50
            rents_2023["rent_burden"] = rents_2023["rent_1R"] / income_2023

            # 3. Merge with geometry
            geo_merged = plr_geo.merge(rents_2023, on="plr_id", how="left")
            gdf_median = gpd.GeoDataFrame(geo_merged, geometry="geometry", crs="EPSG:4326")

            # 4. Convert to GeoJSON
            geojson_dict = json.loads(gdf_median.to_json())

            # 5. Define color scale
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

            # 6. Create the choropleth map
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

            # 7. Customize hover text with order, formatting, and styling
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
            # 7. Styling
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

            # 8. Grey boundaries
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

with tabs[4]:

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

        # Create bar chart of subsidized housing per year
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

        sh_subsidized_totals = sh_subsidized_totals.rename(columns={"new_units": "total_units"})
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

with tabs[5]:
    st.markdown("<div style='margin-top:40px'></div>", unsafe_allow_html=True)
    st.markdown("### Keys Takeaways")
    st.markdown("<div style='margin-top:40px'></div>", unsafe_allow_html=True)

    col1, col2= st.columns([1,24])
    with col1:
        st.markdown("""### <span style='display: inline-flex; align-items: center; justify-content: center; width: 40px; height: 40px; border-radius: 50%; background: #D4583B; color: white; font-weight: bold; margin-right: 10px; font-size: 20px;'>1</span> """, unsafe_allow_html=True)
    with col2:
        st.markdown("##### **Berlin rents have surged**, increasing by 80% on average, and more than **doubling in 129 areas** since 2013.")
        st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)

    col1, col2= st.columns([1,24])
    with col1:
        st.markdown("""### <span style='display: inline-flex; align-items: center; justify-content: center; width: 40px; height: 40px; border-radius: 50%; background: #D4583B; color: white; font-weight: bold; margin-right: 10px; font-size: 20px;'>2</span> """, unsafe_allow_html=True)
    with col2:
        st.markdown("##### **Incomes have grown – but rents have grown faster.** The average rent burden now sits at 34% citywide.")
        st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)

    col1, col2= st.columns([1,24])
    with col1:
        st.markdown("""### <span style='display: inline-flex; align-items: center; justify-content: center; width: 40px; height: 40px; border-radius: 50%; background: #D4583B; color: white; font-weight: bold; margin-right: 10px; font-size: 20px;'>3</span> """, unsafe_allow_html=True)
    with col2:
        st.markdown("##### **Affordability varies depending on income:** Only 43% of planning areas are affordable for **median earners**. For **Bürgergeld recipients**, that drops to just 2.7% of the city.")
        st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)

    col1, col2= st.columns([1,24])
    with col1:
        st.markdown("""### <span style='display: inline-flex; align-items: center; justify-content: center; width: 40px; height: 40px; border-radius: 50%; background: #D4583B; color: white; font-weight: bold; margin-right: 10px; font-size: 20px;'>4</span> """, unsafe_allow_html=True)
    with col2:
        st.markdown("##### **Subsidized housing units are decreasing.** Since 2015, Berlin has lost 58% of its subsidized housing — while demand continues to rise.")
        st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)

    col1, col2= st.columns([1,24])
    with col1:
        st.markdown("""### <span style='display: inline-flex; align-items: center; justify-content: center; width: 40px; height: 40px; border-radius: 50%; background: #D4583B; color: white; font-weight: bold; margin-right: 10px; font-size: 20px;'>5</span> """, unsafe_allow_html=True)
    with col2:
        st.markdown ("##### **Access to housing is becoming increasingly unequal**, shaped by geography, income, and policy limitations.")
        st.markdown("<div style='margin-top:40px'></div>", unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("### Opportunities for Future Analysis")
    st.markdown("""
        Rental affordability is a complex issue shaped by many overlapping factors. While this project offers an overview of how rent prices, income, and social housing access have evolved in Berlin from 2013 to 2023, it does not capture the full complexity of the housing situation. Several important dimensions remain outside the current scope and present opportunities for future analysis:

        - **Heating and utility costs**  
        This analysis focuses on cold rent (*Kaltmiete*), but warm rent (*Warmmiete*) — which includes heating and service charges — would provide a more realistic picture of actual rent burdens.

        - **Household composition and housing needs**  
        Affordability varies significantly depending on household type. Families, single parents, students, and elderly tenants have different spatial and size needs that affect what "affordable" means.

        - **Contract duration and real paid rents**  
        Rent listings reflect market entry prices, not what tenants actually pay. Access to anonymized rent rolls, including contract start dates, would help assess how affordability differs between newcomers and long-term residents.

        - **Inflation-adjusted comparisons**  
        Adjusting both rent and income data for inflation would allow for a clearer understanding of real purchasing power over time.

        - **Market segmentation and ownership structures**  
        Differentiating between private landlords, institutional investors, and public housing companies would provide insight into how different actors shape the affordability landscape.

        - **Lack of rent data distribution within PLRs**  
        This analysis uses median values per planning area, which can mask extreme disparities. Access to more granular rent data would help reveal internal inequalities within neighborhoods.

        - **Tenant protections and legal frameworks**  
        While not covered in this project, policies such as rent caps, tenant protections, and eligibility rules play a critical role in shaping access to affordable housing.

        """)
    st.markdown("---")

    st.markdown("### Outro: Where Could You Afford to Rent?")
    col1, col2 = st.columns([2,5])    
    
    with col1:
        st.markdown("Select your income and apartment size and check how much of your income it would mean.")
        st.markdown("<div style='margin-top:40px'></div>", unsafe_allow_html=True)
        
        # Load data
        rents_df = pd.read_csv("../data/csv/rent/rents_PLR.csv")
        rents_df = rents_df[rents_df["year"] == 2023]
        geojson = gpd.read_file("../data/geo/2021_PLR.geojson")
        geojson = geojson.to_crs(epsg=4326)

        # Standardize keys
        rents_df["plr_id"] = rents_df["plr_id"].astype(str).str.zfill(8)
        geojson["PLR_ID"] = geojson["PLR_ID"].astype(str)

        # Merge datasets
        merged = geojson.merge(rents_df, left_on="PLR_ID", right_on="plr_id")

        # Ensure numeric prices
        merged["median"] = pd.to_numeric(merged["median"], errors="coerce")

        apartment_options = {
            "1-room (50 m²)": 50,
            "2-room (65 m²)": 65,
            "3-room (80 m²)": 80
        }

        income = st.slider("Select your monthly income (€)", 500, 5000, 1500, step=50)
        st.markdown("<div style='margin-top:40px'></div>", unsafe_allow_html=True)

        size_label = st.selectbox("Apartment size", options=list(apartment_options.keys()))
        st.markdown("<div style='margin-top:40px'></div>", unsafe_allow_html=True)

        apartment_size = apartment_options[size_label]

        # Compute rent burden
        merged["estimated_rent"] = merged["median"] * apartment_size
        merged["rent_burden"] = merged["estimated_rent"] / income

        # Filter out missing rent burden
        valid_data = merged[merged["rent_burden"].notna()]

        # Count affordable PLRs
        affordable_count = (valid_data["rent_burden"] <= 0.30).sum()
        st.metric(label="Number of Affordable PLRs", value=f"{affordable_count}")

    with col2:
        custom_scale = [
        [0.00, 'rgba(224,243,219,0.6)'],
        [0.15, 'rgba(168,221,181,0.6)'],
        [0.30, 'rgba(65,177,122,0.6)'],
        [0.40, 'rgba(254,204,92,0.6)'],
        [0.50, 'rgba(253,141,60,0.6)'],
        [0.60, 'rgba(240,59,32,0.6)'],
        [1.00, 'rgba(189,0,38,0.6)']]

        your_rent = go.Figure(go.Choroplethmapbox(
            geojson=json.loads(geojson.to_json()),  
            locations=valid_data["PLR_ID"],
            featureidkey="properties.PLR_ID",
            z=valid_data["rent_burden"],
            colorscale=custom_scale,
            zmin=0,
            zmax=1.0,
            marker_line_width=0.2,
            marker_line_color="white",
            colorbar=dict(
                title="Rent Burden %",
                tickformat=".0%",
                tickvals=[0.0, 0.3, 1],
                ticktext=["0%", "30%", "100%"],
                len=0.3,
                thickness=15,
                y=0.05,
                x=0.01,
                xanchor="left",
                yanchor="bottom"
            ),
            hovertext=valid_data.apply(
                lambda row: f"{row['PLR_NAME']}<br>Rent Burden: {row['rent_burden']:.0%}", axis=1
            ),
            hoverinfo="text",
            name="Rent Burden"
        ))

        your_rent.update_traces(
            marker_line_color="gray",
            marker_line_width=0.5,
            hoverlabel=dict(
                font_size=16,
                font_family="Arial",
                font_color="black"
            )
        )

        your_rent.update_layout(
            mapbox_style="carto-positron",
            mapbox_zoom=10,
            mapbox_center={"lat": 52.52, "lon": 13.405},
            dragmode='zoom',
            height=900,
            margin=dict(l=0, r=0, t=0, b=0)
        )

        st.plotly_chart(your_rent, use_container_width=True)

    st.markdown("---")

    st.markdown("### Credits")
    with st.expander("", expanded=True):
        st.markdown("###### Juni 2024")
        st.markdown("This data analysis project is the capstone project at the end of the Data Analytics Bootcamp at Spiced Academy.")
        st.markdown("###### Concept and Design")
        st.markdown("""
            <a href="https://www.ivan-alfonsoburgos.com/" target="_blank" style="text-decoration: underline; color: #D4583B;">Iván Alfonso Burgos</a>
            """, unsafe_allow_html=True)
        st.markdown("###### Source Code")
        st.markdown("""
            <a href="https://github.com/ivan13f/affordable-for-whom" target="_blank" style="text-decoration: underline; color: #D4583B;">Github</a>
            """, unsafe_allow_html=True)
        st.markdown("###### Sources")
        st.markdown("""
            <a href="https://www.berlin.de/sen/wohnen/service/berliner-wohnungsmarkt/wohnatlas-berlin/" target="_blank" style="text-decoration: underline; color: #D4583B;">Wohnatlas Berlin 2022</a>
            """, unsafe_allow_html=True)
        st.markdown("""
            <a href="https://www.ibb.de/de/ueber-uns/publikationen/wohnungsmarktbericht/2024.html#iframe_angebotsmieten/" target="_blank" style="text-decoration: underline; color: #D4583B;">IBB Wohnungsmarktbericht 2024</a>
            """, unsafe_allow_html=True)
        st.markdown("""
            <a href="https://www.statistischebibliothek.de/mir/servlets/solr/find?condQuery=Statistischer+Bericht+%2F+A+%2F+I+%2F+16" target="_blank" style="text-decoration: underline; color: #D4583B;">Statistischer Bericht  A I 16 – hj 1/ 24 Einwohnerregisterstatistik</a>
            """, unsafe_allow_html=True)
        st.markdown("""
            <a href="https://inberlinwohnen.de/kennzahlen/" target="_blank" style="text-decoration: underline; color: #D4583B;">Die landeseigene Wohnungswirtschaft in Zahlen</a>
            """, unsafe_allow_html=True)   
        st.markdown("""
            <a href="https://www.statistik-berlin-brandenburg.de/p-i-10-j" target="_blank" style="text-decoration: underline; color: #D4583B;">Primäreinkommen und verfügbares Einkommen der privaten Haushalte 1991 bis 2022</a>
            """, unsafe_allow_html=True)       

    st.markdown("---")
