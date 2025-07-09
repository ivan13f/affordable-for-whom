import pandas as pd
import geopandas as gpd
import streamlit as st
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
IMAGES_DIR = os.path.join(BASE_DIR, "images")

@st.cache_data
def load_rents_PLR():
    file_path = os.path.join(BASE_DIR, "data", "csv", "rent", "rents_PLR.csv")
    rents_PLR = pd.read_csv(file_path, sep=",")
    #rents_PLR["plr_id"] = rents_PLR["plr_id"].astype(str).str.zfill(8)
    return rents_PLR

@st.cache_data
def load_rents_BEZ():
    file_path = os.path.join(BASE_DIR, "data", "csv", "rent", "rents_BEZ.csv")
    rents_BEZ = pd.read_csv(file_path, sep=",")
    #rents_BEZ["plr_id"] = rents_BEZ["plr_id"].astype(str).str.zfill(8)
    return rents_BEZ

@st.cache_data
def load_rent_structure():
    file_path = os.path.join(BASE_DIR, "data", "csv", "rent", "rent_price_structure_2023.csv")
    rent_structure = pd.read_csv(file_path)
    return rent_structure

@st.cache_data
def load_pop_BEZ():
    file_path = os.path.join(BASE_DIR, "data", "csv", "population", "population_BEZ.csv")
    pop_BEZ = pd.read_csv(file_path)
    return pop_BEZ

@st.cache_data
def load_net_migration():
    file_path = os.path.join(BASE_DIR, "data", "csv", "population", "net_migration_BEZ.csv")
    net_migration = pd.read_csv(file_path)
    return net_migration

@st.cache_data
def load_income_persons():
    file_path = os.path.join(BASE_DIR, "data", "csv", "income", "disposable_income.csv")
    income_persons = pd.read_csv(file_path)
    return income_persons

@st.cache_data
def load_income_households():
    file_path = os.path.join(BASE_DIR, "data", "csv", "income", "income_household_13_23.csv")
    income_households = pd.read_csv(file_path)
    return income_households

@st.cache_data
def load_wohnatlas_2022():
    file_path = os.path.join(BASE_DIR, "data", "csv", "wohnatlas", "wohnatlas_2022.csv")
    wohnatlas_2022 = pd.read_csv(file_path)
    return wohnatlas_2022

@st.cache_data
def load_wbs_berlin():
    file_path = os.path.join(BASE_DIR, "data", "csv", "public_housing", "wbs_berlin.csv")
    wbs_berlin = pd.read_csv(file_path)
    return wbs_berlin

@st.cache_data
def load_subsidies():
    file_path = os.path.join(BASE_DIR, "data", "csv", "public_housing", "social_housing_subsidized_berlin.csv")
    subsidies = pd.read_csv(file_path)
    return subsidies

@st.cache_data
def load_sh_subsidized_totals():
    file_path = os.path.join(BASE_DIR, "data", "csv", "public_housing", "sh_subsidized_totals.csv")
    sh_subsidized_totals = pd.read_csv(file_path, sep=";", encoding="utf-8")
    return sh_subsidized_totals

@st.cache_data
def load_plr_geo():
    file_path = os.path.join(BASE_DIR, "data", "geo", "2021_PLR.geojson")
    plr_geo = gpd.read_file(file_path).to_crs(epsg=4326)
    plr_geo = plr_geo.rename(columns={
    "PLR_ID": "plr_id",
    "PLR_NAME": "plr_name",
    "BEZ": "bez_id"})
    plr_geo["plr_id"] = plr_geo["plr_id"].astype(int)
    plr_geo["bez_id"] = plr_geo["bez_id"].astype(int)
    return plr_geo

@st.cache_data
def load_pgr_geo():
    file_path = os.path.join(BASE_DIR, "data", "geo", "2021_PGR.geojson")
    pgr_geo = gpd.read_file(file_path).to_crs(epsg=4326)
    pgr_geo = pgr_geo.rename(columns={
        "PGR_ID": "pgr_id",
        "PGR_NAME": "pgr_name",
        "BEZ": "bez_id"})
    pgr_geo["pgr_id"] = pgr_geo["pgr_id"].astype(int)
    pgr_geo["bez_id"] = pgr_geo["bez_id"].astype(int)
    return pgr_geo
