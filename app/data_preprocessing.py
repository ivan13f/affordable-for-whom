import pandas as pd
import geopandas as gpd

from data_loader import load_rents_BEZ, load_income_persons, load_income_households, load_rents_PLR, load_plr_geo

rents_PLR = load_rents_PLR()
rents_BEZ = load_rents_BEZ()
income_persons = load_income_persons()
income_households = load_income_households()
plr_geo = load_plr_geo()


def get_rent_burden() -> pd.DataFrame:
    """Calculate the rent burden for 1-room apartments based on median rents and monthly disposable income."""
    rents_by_year = (
        rents_BEZ
        .groupby('year')['median']
        .mean()
        .reset_index()
        .loc[lambda d: d["year"].between(2013, 2023)]
    )
    combined = (
        income_persons
        .loc[lambda d: d["year"].between(2013, 2023)]
        .rename(columns={"monthly_disposable_income": "monthly_available_income"})
        .loc[:, ['year', 'monthly_available_income']]
        .merge(rents_by_year, on='year',how='inner')
        .assign(
            rent_1R=lambda d: (d["median"] * 50).round(0),
            rent_burden=lambda d: (d["rent_1R"] / d["monthly_available_income"] * 100).round(0)
        )
    )

    return combined


def get_rent_burden_and_income():

    income_buergergeld = 1143

    # Get median income for Berlin 2023
    income_2023 = (
        income_households
        .loc[lambda d: d["year"] == 2023, "monthly_available_income"]
        .values[0]
    )

    # Filter rent prices for 2023 and calculate 1R rent & rent burden
    geo_merged = gpd.GeoDataFrame(
        (
            rents_PLR
            .loc[lambda d: d["year"] == 2023, ["plr_id", "median"]]
            .assign(
                rent_1R=lambda d: d["median"] * 50,
                rent_burden_median_income=lambda d: d["rent_1R"] / income_2023,
                rent_burden_bg=lambda d: d["rent_1R"] / income_buergergeld
            )
            .merge(plr_geo, on="plr_id", how="left")
        ),
        geometry="geometry",
        crs="EPSG:4326"
    )

    return geo_merged
