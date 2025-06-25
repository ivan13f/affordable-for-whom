import streamlit as st
import pandas as pd
import geopandas as gpd
import json
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(layout="wide")

plr_geo = gpd.read_file("data/geo/2021_PLR.geojson")
plr_geo = plr_geo.to_crs(epsg=4326)
plr_geo = plr_geo.rename(columns={
    "PLR_ID": "plr_id",
    "PLR_NAME": "plr_name",
    "BEZ": "bez_id"
})
plr_geo["plr_id"] = plr_geo["plr_id"].astype(int)
plr_geo["bez_id"] = plr_geo["bez_id"].astype(int)

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

st.markdown("---")

st.markdown("### Outro: Where Could You Afford to Rent?")
col1, col2 = st.columns([2,5])    

with col1:
    st.markdown("Select your income and apartment size and check how much of your income it would mean.")
    st.markdown("<div style='margin-top:40px'></div>", unsafe_allow_html=True)
    
    # Load data
    rents_df = pd.read_csv("data/csv/rent/rents_PLR.csv")
    rents_df = rents_df[rents_df["year"] == 2023]
    geojson = gpd.read_file("data/geo/2021_PLR.geojson")
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
