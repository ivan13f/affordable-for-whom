import streamlit as st

from tabs import (
    show_intro_tab,
    show_supply_tab,
    show_demand_tab,
    show_affordability_tab,
    show_social_tab,
    show_outlook_tab)

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
            
    .stMarkdown a, .scroll-button {
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

tabs = st.tabs([
    "Intro", "Supply", "Demand",
    "Affordability", "Social Housing", "Outlook"
])

with tabs[0]:
    show_intro_tab()
with tabs[1]:
    show_supply_tab()
with tabs[2]:
    show_demand_tab()
with tabs[3]:
    show_affordability_tab()
with tabs[4]:
    show_social_tab()
with tabs[5]:
    show_outlook_tab()
