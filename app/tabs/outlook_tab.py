import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.graph_objects as go
import plotly.express as px
import json
from data_loader import load_rents_PLR, load_plr_geo

rents_PLR = load_rents_PLR()
plr_geo = load_plr_geo()

def show_outlook_tab():
    st.markdown("<div style='margin-top:40px'></div>", unsafe_allow_html=True)
    st.markdown("### Keys Takeaways")
    st.markdown("<div style='margin-top:40px'></div>", unsafe_allow_html=True)

    col1, col2 = st.columns([1,24])
    with col1:
        st.markdown("""### <span style='display: inline-flex; align-items: center; justify-content: center; width: 40px; height: 40px; border-radius: 50%; background: #D4583B; color: white; font-weight: bold; margin-right: 10px; font-size: 20px;'>1</span> """, unsafe_allow_html=True)
    st.markdown("<div style='margin-top:10px'></div>", unsafe_allow_html=True) 
    with col2:
        st.markdown("##### **Berlin rents have surged**, increasing by 80% on average, and more than **doubling in 129 areas** since 2013.")
    
    col1, col2= st.columns([1,24])
    with col1:
        st.markdown("""### <span style='display: inline-flex; align-items: center; justify-content: center; width: 40px; height: 40px; border-radius: 50%; background: #D4583B; color: white; font-weight: bold; margin-right: 10px; font-size: 20px;'>2</span> """, unsafe_allow_html=True)
    st.markdown("<div style='margin-top:10px'></div>", unsafe_allow_html=True)
    with col2:
        st.markdown("##### **Incomes have grown – but rents have grown faster.** The average rent burden now sits at 34% citywide.")

    col1, col2= st.columns([1,24])
    with col1:
        st.markdown("""### <span style='display: inline-flex; align-items: center; justify-content: center; width: 40px; height: 40px; border-radius: 50%; background: #D4583B; color: white; font-weight: bold; margin-right: 10px; font-size: 20px;'>3</span> """, unsafe_allow_html=True)
    st.markdown("<div style='margin-top:10px'></div>", unsafe_allow_html=True)
    with col2:
        st.markdown("##### **Affordability varies depending on income:** Only 43% of planning areas are affordable for **median earners**. For **Bürgergeld recipients**, that drops to just 2.7% of the city.")

    col1, col2= st.columns([1,24])
    with col1:
        st.markdown("""### <span style='display: inline-flex; align-items: center; justify-content: center; width: 40px; height: 40px; border-radius: 50%; background: #D4583B; color: white; font-weight: bold; margin-right: 10px; font-size: 20px;'>4</span> """, unsafe_allow_html=True)
    st.markdown("<div style='margin-top:10px'></div>", unsafe_allow_html=True)
    with col2:
        st.markdown("##### **Subsidized housing units are decreasing.** Since 2015, Berlin has lost 58% of its subsidized housing — while demand continues to rise.")

    col1, col2= st.columns([1,24])
    with col1:
        st.markdown("""### <span style='display: inline-flex; align-items: center; justify-content: center; width: 40px; height: 40px; border-radius: 50%; background: #D4583B; color: white; font-weight: bold; margin-right: 10px; font-size: 20px;'>5</span> """, unsafe_allow_html=True)
    st.markdown("<div style='margin-top:10px'></div>", unsafe_allow_html=True)
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
        percentage = round((affordable_count / 542) * 100)
        st.metric(
            label="Number of Affordable Planning Areas",
            value=f"{affordable_count} / 542 ({percentage}%)")

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
        st.markdown("###### June 2025")
        st.markdown("This project is the capstone project at the end of the Data Analytics Bootcamp at Spiced Academy.")
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