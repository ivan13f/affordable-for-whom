#!/usr/bin/env python3
"""Precompute every chart of the Streamlit app into static JSON for the site in docs/.

The Streamlit app recomputed all figures on every start. This script runs the same
pandas/geopandas logic once and writes plain JSON files that docs/assets/app.js
renders with Plotly.js in the browser. Re-run it only when the data changes:

    pip install pandas geopandas plotly
    python scripts/build_static.py
"""
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "data" / "csv"
GEO = ROOT / "data" / "geo"
OUT = ROOT / "docs" / "data"

# Plotly's old "mapbox" traces load CARTO's retired raster CDN, which now only serves
# "API KEY REQUIRED" tiles. The MapLibre "map" traces use CARTO's vector Positron
# style instead, which works without a key.
MAP_STYLE = "carto-positron"
ACCENT = "#D4583B"
SIMPLIFY_TOLERANCE = 0.001  # degrees, same as the Streamlit app
COORD_DECIMALS = 5          # ~1 m, keeps the GeoJSON small
# Plotly.js 4 aligns an overlaid axis' ticks with the main axis by default, so the
# secondary y axes below set tickmode="auto" to keep their own ticks, as in Plotly 3.


# ---- LOADING ----

def read_csv(*parts, **kwargs):
    return pd.read_csv(CSV.joinpath(*parts), **kwargs)


def comma_float(series):
    return series.astype(str).str.replace(",", ".", regex=False).astype(float)


def load_geo(filename, prefix):
    key = prefix.lower()
    gdf = gpd.read_file(GEO / filename).to_crs(epsg=4326)
    gdf = gdf.rename(columns={f"{prefix}_ID": f"{key}_id", f"{prefix}_NAME": f"{key}_name", "BEZ": "bez_id"})
    gdf[f"{key}_id"] = gdf[f"{key}_id"].astype(int)
    gdf["bez_id"] = gdf["bez_id"].astype(int)
    gdf["geometry"] = gdf["geometry"].simplify(tolerance=SIMPLIFY_TOLERANCE, preserve_topology=True)
    return gdf


def round_coords(value):
    if isinstance(value, float):
        return round(value, COORD_DECIMALS)
    if isinstance(value, (list, tuple)):
        return [round_coords(v) for v in value]
    return value


def to_geojson(gdf, id_col):
    """Geometry only; names and values travel with each figure's hover data."""
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {id_col: int(fid)},
                "geometry": {"type": geom.geom_type, "coordinates": round_coords(geom.__geo_interface__["coordinates"])},
            }
            for fid, geom in zip(gdf[id_col], gdf["geometry"])
        ],
    }


rents_PLR = read_csv("rent", "rents_PLR.csv")
rents_BEZ = read_csv("rent", "rents_BEZ.csv")
rents_BEZ["bez_name"] = rents_BEZ["bez_name"].str.strip()
rent_structure = read_csv("rent", "rent_price_structure_2023.csv")
pop_BEZ = read_csv("population", "population_BEZ.csv")
pop_BEZ["bez_name"] = pop_BEZ["bez_name"].str.strip()
net_migration = read_csv("population", "net_migration_BEZ.csv")
net_migration["bez_name"] = net_migration["bez_name"].str.strip()
income_persons = read_csv("income", "disposable_income.csv")
income_persons["monthly_disposable_income"] = comma_float(income_persons["monthly_disposable_income"])
income_households = read_csv("income", "income_household_13_23.csv")
wohnatlas_2022 = read_csv("wohnatlas", "wohnatlas_2022.csv").rename(columns=lambda c: c.strip())
wbs_berlin = read_csv("public_housing", "wbs_berlin.csv")
subsidies = read_csv("public_housing", "social_housing_subsidized_berlin.csv")
sh_subsidized_totals = read_csv("public_housing", "sh_subsidized_totals.csv", sep=";")

plr_geo = load_geo("2021_PLR.geojson", "PLR")
pgr_geo = load_geo("2021_PGR.geojson", "PGR")
PLR_GEOJSON = to_geojson(plr_geo, "plr_id")
PGR_GEOJSON = to_geojson(pgr_geo, "pgr_id")


# ---- SERIALISATION ----

def fig_json(fig, geo=None):
    """Figure as a plain dict. Map traces get a "@plr"/"@pgr" placeholder instead of the
    GeoJSON (shared files loaded once in the browser), and the Plotly template is
    dropped because app.js applies the Streamlit theme to every chart."""
    d = json.loads(fig.to_json())
    d["layout"].pop("template", None)
    traces = d["data"] + [t for frame in d.get("frames", []) for t in frame.get("data", [])]
    for trace in traces:
        if "geojson" in trace:
            trace["geojson"] = geo
    return d


def write_json(name, payload):
    path = OUT / name
    path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"  {path.relative_to(ROOT)}  {path.stat().st_size / 1024:,.0f} KB")


# ---- INTRO TAB ----

def intro_rent_map():
    gdf = rents_PLR[rents_PLR["year"].between(2013, 2023) & rents_PLR["plr_id"].isin(plr_geo["plr_id"])].copy()
    vmin, vmax = gdf["median"].min(), gdf["median"].max()
    years = sorted(gdf["year"].unique())

    fig = px.choropleth_map(
        gdf.sort_values("year"),
        geojson=PLR_GEOJSON,
        locations="plr_id",
        featureidkey="properties.plr_id",
        color="median",
        hover_name="plr_name",
        hover_data={"plr_id": False},
        animation_frame="year",
        color_continuous_scale="YlOrRd",
        range_color=(vmin, vmax),
        map_style=MAP_STYLE,
        zoom=9.7,
        center={"lat": 52.49, "lon": 13.405},
        opacity=0.7,
        labels={"median": "Median Rent (€/m²)", "year": "Year "},
    )
    fig.update_layout(
        height=800,
        title="",
        margin=dict(r=0, t=0, l=0, b=0),
        coloraxis_colorbar=dict(
            title="Median<br>Rent (€/m²)",
            title_font=dict(size=16, color="black", weight="bold"),
            tickfont=dict(size=14, color="black"),
            x=0.997, xanchor="right", y=0.55, yanchor="middle", len=0.85),
        updatemenus=[{
            "type": "buttons",
            "buttons": [
                {"label": "Play", "method": "animate", "args": [None, {
                    "frame": {"duration": 1500, "redraw": True},
                    "fromcurrent": True,
                    "transition": {"duration": 500},
                    "mode": "immediate"}]},
                {"label": "Pause", "method": "animate", "args": [[None], {
                    "frame": {"duration": 0, "redraw": False},
                    "mode": "immediate"}]},
            ],
            "font": {"size": 14, "color": "black"},
            "x": 0.1, "y": 0.2, "direction": "left"}],
        sliders=[{
            "active": 0,
            "font": {"size": 16, "color": "black"},
            "currentvalue": {"prefix": "Year ", "visible": True,
                             "font": {"size": 16, "color": "black", "family": "Arial Black"}},
            "steps": [{"label": str(y), "method": "animate", "args": [[str(y)], {
                "frame": {"duration": 0, "redraw": True}, "mode": "immediate"}]} for y in years],
            "x": 0.11, "y": 0.22, "len": 0.85}],
    )
    fig.update_traces(marker_line_color="gray", marker_line_width=0.5,
                      hoverlabel=dict(font_size=16, font_family="Arial", font_color="black"))
    return fig


# ---- SUPPLY TAB ----

def rent_series(district):
    rents = rents_BEZ[rents_BEZ["year"].between(2013, 2023)]
    if district == "All Berlin":
        # "All Berlin" is the average of district-level medians
        by_district = rents.groupby(["year", "bez_name"])["median"].mean().reset_index()
        return by_district.groupby("year")["median"].mean().loc[2013:2023]
    return rents[rents["bez_name"] == district].groupby("year")["median"].mean().loc[2013:2023]


def supply_rent_yoy(district):
    filtered = rent_series(district)
    yoy = (filtered.pct_change() * 100).round(2)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=yoy.index, y=yoy.values, name="Yearly Increase (%)", marker_color=ACCENT, yaxis="y",
        text=[f"{v:.2f}%" if pd.notna(v) else "" for v in yoy], textposition="outside",
        textfont=dict(color=ACCENT, size=14, family="Arial", weight="bold"), offsetgroup=0))
    fig.add_trace(go.Scatter(
        x=filtered.index, y=filtered.values, name="Median Rent (€/m²)", mode="lines+markers",
        line=dict(color="black", width=2.5), marker=dict(size=8, color="black"), yaxis="y2"))
    fig.add_annotation(
        x=filtered.index[0], y=-1, text=f"{filtered.iloc[0]:.2f} €/m²", showarrow=False,
        xanchor="left", yanchor="top", xshift=10, yshift=-10, bgcolor="black",
        font=dict(color="white", size=16), borderpad=4)
    fig.add_annotation(
        x=filtered.index[-1], y=filtered.iloc[-1], text=f"{filtered.iloc[-1]:.2f} €/m²", showarrow=False,
        xanchor="right", yanchor="middle", bgcolor="black", font=dict(color="white", size=16), borderpad=4)
    fig.add_shape(type="line", x0=2012.6, x1=2023.6, y0=0, y1=0, xref="x", yref="y",
                  line=dict(color="black", width=1.5), layer="above")
    fig.update_layout(
        xaxis=dict(tickmode="linear", dtick=1, tickfont=dict(size=14, color="black"),
                   showgrid=False, showline=True, linecolor="black", linewidth=1),
        yaxis=dict(title=dict(text="Yearly Increase (%)", font=dict(color="black")), tickfont=dict(color="black"),
                   showgrid=False, showline=True, linecolor="black", linewidth=1),
        yaxis2=dict(title=dict(text="Median Rent (€/m²)", font=dict(color="black")), tickfont=dict(color="black"),
                    overlaying="y", tickmode="auto", side="right", showgrid=False, showline=True, linecolor="black", linewidth=1),
        plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
        legend=dict(x=0.01, y=0.99, font=dict(size=15)), showlegend=True,
        bargap=0.3, height=600, margin=dict(l=60, r=60, t=40, b=40), title="")
    return fig


def supply_increase_map():
    rents_2013 = rents_PLR[rents_PLR["year"] == 2013][["plr_id", "median"]].rename(columns={"median": "rent_2013"})
    rents_2023 = rents_PLR[rents_PLR["year"] == 2023][["plr_id", "median"]].rename(columns={"median": "rent_2023"})
    rents_change = rents_2013.merge(rents_2023, on="plr_id", how="inner")
    rents_change["pct_increase"] = (rents_change["rent_2023"] - rents_change["rent_2013"]) / rents_change["rent_2013"] * 100
    gdf = pd.DataFrame(plr_geo[["plr_id", "plr_name"]]).merge(rents_change, on="plr_id", how="left")

    named = rents_change.merge(plr_geo[["plr_id", "plr_name"]], on="plr_id", how="left")
    max_plr = named.loc[named["pct_increase"].idxmax()]
    min_plr = named.loc[named["pct_increase"].idxmin()]
    kpis = {
        "max": {"value": f"{max_plr['pct_increase']:.1f}%", "name": max_plr["plr_name"]},
        "min": {"value": f"{min_plr['pct_increase']:.1f}%", "name": min_plr["plr_name"]},
    }

    # Diverging scale: greys for negatives, red-orange for positives
    scale = [[0.00, "#AAAAAA"], [0.05, "#CCCCCC"], [0.09, "#EEEEEE"], [0.25, "#FFE3A7"],
             [0.50, "#FC9E5A"], [0.75, "#F03B20"], [1.00, "#BD0026"]]

    fig = px.choropleth_map(
        gdf, geojson=PLR_GEOJSON, locations="plr_id", featureidkey="properties.plr_id",
        color="pct_increase", color_continuous_scale=scale, range_color=(-40, 300),
        map_style=MAP_STYLE, zoom=9.5, center={"lat": 52.52, "lon": 13.405}, opacity=0.8,
        hover_name="plr_name",
        hover_data={"plr_id": False, "rent_2013": ":.2f", "rent_2023": ":.2f", "pct_increase": ":.1f"},
        labels={"plr_name": "PLR Name", "rent_2013": "Rent 2013 (€/m²)",
                "rent_2023": "Rent 2023 (€/m²)", "pct_increase": "Increase (%)"})
    fig.update_layout(
        coloraxis_colorbar=dict(
            title="Rent Change (%)", orientation="v", x=0.99, y=0.5, xanchor="right", yanchor="middle",
            len=0.75, thickness=12, tickvals=[-40, 0, 50, 100, 200, 287],
            ticktext=["-40%", "0%", "50%", "100%", "200%", "287%"],
            title_font=dict(size=12, color="black"), tickfont=dict(size=12, color="black")),
        margin=dict(t=0, b=0, l=0, r=0), height=600)
    fig.update_traces(marker_line_color="gray", marker_line_width=0.5,
                      hoverlabel=dict(font_size=16, font_family="Arial", font_color="black"))
    return fig, kpis


def supply_district_bars():
    rents = rents_BEZ[rents_BEZ["year"].isin([2013, 2023])].copy()
    rents["year"] = rents["year"].astype(str)
    pivot = rents.pivot(index="bez_name", columns="year", values="median").reset_index()
    pivot["pct_increase"] = ((pivot["2023"] - pivot["2013"]) / pivot["2013"] * 100).round(1)
    pivot["label"] = pivot["pct_increase"].astype(str) + "% increase"
    pivot = pivot.sort_values("2023", ascending=False)

    fig = go.Figure()
    fig.add_trace(go.Bar(y=pivot["bez_name"], x=pivot["2013"], name="2013", marker_color="lightgrey", orientation="h"))
    fig.add_trace(go.Bar(
        y=pivot["bez_name"], x=pivot["2023"], name="2023", marker_color=ACCENT, orientation="h",
        text=pivot["label"], textposition="outside", cliponaxis=False, insidetextanchor="start",
        textfont=dict(color=ACCENT, size=13, family="Arial", weight="bold")))
    fig.update_layout(
        yaxis=dict(title=None, tickfont=dict(size=12, color="black"), showgrid=False, showline=True,
                   linecolor="black", linewidth=1, autorange="reversed"),
        xaxis=dict(title="Median Rent (€/m²)", tickfont=dict(size=12, color="black"), showgrid=False,
                   zeroline=False, showline=True, linecolor="black", linewidth=1,
                   range=[0, max(pivot["2023"]) * 1.2], fixedrange=True),
        barmode="group", bargap=0.4, plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
        legend=dict(x=1.0, y=0, xanchor="right", yanchor="bottom", orientation="v",
                    font=dict(size=14, color="black")),
        height=600, margin=dict(l=120, r=120, t=30, b=40), title="")
    fig.update_traces(hoverlabel=dict(font_size=14, font_family="Arial", font_color="black"))
    return fig


def supply_segmentation():
    structure = rent_structure.copy()
    structure.loc[structure["Bezirk"] == "Berlin insgesamt", "Bezirk"] = "Total Berlin"
    main = structure[structure["Bezirk"] != "Total Berlin"]
    total = structure[structure["Bezirk"] == "Total Berlin"]
    df = pd.concat([main.sort_values(by="≥18 EUR/m²", ascending=False), total], ignore_index=True)

    # Expensive → affordable, darkest first
    price_columns = list(reversed([c for c in rent_structure.columns if c != "Bezirk"]))
    colors = ["#D4583B", "#D94425", "#ED4F2D", "#F86A3C", "#FC8C5C", "#FDB99B", "#FEE2D5"]
    order = df["Bezirk"].tolist()
    order = order[:-1][::-1] + [order[-1]]

    fig = go.Figure()
    offsets = {bez: 0 for bez in df["Bezirk"]}
    for i, col in enumerate(price_columns):
        for bez, value in zip(df["Bezirk"], df[col]):
            if bez == "Total Berlin":
                # Percentage labels only on the "Total Berlin" bar
                fig.add_annotation(x=value / 2 + offsets[bez], y=bez, text=f"{value}%", showarrow=False,
                                   font=dict(color="white", size=12, family="Arial"),
                                   xanchor="center", yanchor="middle")
            offsets[bez] += value
        fig.add_trace(go.Bar(
            y=df["Bezirk"], x=df[col], name=col, orientation="h", marker=dict(color=colors[i]),
            textposition="none", hovertemplate=f"{col}: %{{x}}<extra></extra>"))
    fig.update_layout(
        barmode="stack",
        xaxis=dict(title="Share of Listings (%)", ticksuffix="%", tickfont=dict(size=16, color="black"),
                   range=[0, 100], showline=True, linecolor="black", linewidth=1),
        yaxis=dict(title=None, type="category", categoryorder="array", categoryarray=order,
                   showline=True, linecolor="black", linewidth=1, tickfont=dict(size=12, color="black")),
        plot_bgcolor="#ffffff", paper_bgcolor="#ffffff", height=600,
        margin=dict(l=140, r=40, t=30, b=40),
        legend=dict(title="Monthly Cold Rent", title_font=dict(size=14, color="black", weight="bold"),
                    font=dict(size=12, color="black"), traceorder="normal",
                    yanchor="top", y=1, xanchor="left", x=1.02),
        title="")
    fig.update_traces(hoverlabel=dict(font_size=16, font_family="Arial", font_color="black"))
    return fig


# ---- DEMAND TAB ----

def demand_pop_migration(option):
    if option == "All Berlin":
        pop = pop_BEZ.groupby("year")["population"].sum().reset_index()
        mig = (net_migration[net_migration["bez_name"] != "Berlin Insgesamt"]
               .groupby("year")["net_migration"].sum().reset_index())
    else:
        pop = pop_BEZ[pop_BEZ["bez_name"] == option][["year", "population"]]
        mig = net_migration[net_migration["bez_name"] == option][["year", "net_migration"]]
    growth = pop.merge(mig, on="year", how="inner").sort_values("year")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=growth["year"], y=growth["population"], name="Total Population", mode="lines+markers",
        line=dict(color="black", width=2), marker=dict(size=8, color="black"), yaxis="y1",
        hovertemplate="Total Population: %{y:,}<extra></extra>"))
    fig.add_trace(go.Bar(
        x=growth["year"], y=growth["net_migration"], base=0, name="Net Migration", marker_color=ACCENT,
        yaxis="y2", width=0.5, text=[f"{v:,}" for v in growth["net_migration"]], textposition="outside",
        textfont=dict(color=ACCENT, size=13, family="Arial Black"),
        hovertemplate="Net Migration: %{y:,}<extra></extra>"))
    if not growth.empty:
        ends = [0, -1] if len(growth) > 1 else [0]
        for i in ends:
            fig.add_annotation(
                x=growth["year"].iloc[i], y=growth["population"].iloc[i] * 0.98,
                text=f"{growth['population'].iloc[i]:,}", showarrow=False, xanchor="center", yanchor="top",
                font=dict(color="white", size=16), bgcolor="black", borderpad=4)
    fig.add_shape(type="line", xref="paper", yref="y2", x0=0, x1=1, y0=0, y1=0, line=dict(color="black", width=2))
    fig.update_layout(
        height=600, plot_bgcolor="white", paper_bgcolor="white", bargap=0,
        xaxis=dict(title=None, tickmode="linear", dtick=1, tickfont=dict(size=16, color="black"), showline=True,
                   ticks="outside", showgrid=False, linecolor="black", automargin=False, constrain="domain"),
        yaxis=dict(title=dict(text="Total Population", font=dict(color="black")),
                   tickfont=dict(size=16, color="black"), showline=True, showgrid=False, linecolor="black",
                   rangemode="tozero", automargin=False, constrain="domain"),
        yaxis2=dict(title=dict(text="Net Migration", font=dict(color="black")),
                    tickfont=dict(size=16, color="black"), range=[0, 180000], overlaying="y", tickmode="auto", side="right",
                    showline=True, showgrid=False, linecolor="black", automargin=False, constrain="domain"),
        legend=dict(x=0.01, y=1.02, font=dict(size=16, color="black")),
        margin=dict(l=80, r=80, t=40, b=40),
        hoverlabel=dict(font_size=16, font_family="Arial", font_color="black"))
    return fig


def demand_income_line():
    last_year = income_persons["year"].iloc[-1]
    last_value = income_persons["monthly_disposable_income"].iloc[-1]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=income_persons["year"], y=income_persons["monthly_disposable_income"], mode="lines+markers",
        name="Monthly Net Income", line=dict(color="black", width=2), marker=dict(size=6, color="black"),
        hovertemplate="Year: %{x}<br>Income: %{y:.2f} €<extra></extra>"))
    fig.add_annotation(x=last_year, y=last_value, text=f"{last_value:.2f} €", showarrow=False,
                       xanchor="center", yanchor="top", font=dict(color="white", size=16, weight="bold"),
                       bgcolor="black", borderpad=4)
    fig.update_layout(
        height=600, plot_bgcolor="white", paper_bgcolor="white", margin=dict(l=60, r=60, t=40, b=60),
        xaxis=dict(title=None, tickmode="linear", dtick=2, tickfont=dict(size=14, color="black"),
                   showline=True, linecolor="black"),
        yaxis=dict(title="Monthly Disposable Income (€)", tickfont=dict(color="black"), showline=True,
                   rangemode="tozero", linecolor="black"),
        legend=dict(x=0.01, y=0.99, font=dict(size=12, color="black")))
    return fig


def demand_income_stack():
    cols = ["%_under_900", "%_900_1500", "%_1500_2600", "%_2600_4500", "%_over_4500"]
    households = income_households.copy()
    for col in cols:
        households[col] = comma_float(households[col])
    colors = ["#FEE2D5", "#FDB99B", "#FC8C5C", "#F86A3C", "#D4583B"]

    fig = go.Figure()
    for col, color in zip(cols, colors):
        label = col.replace("%_", "").replace("_", "–").replace("over", "Over ")
        fig.add_trace(go.Scatter(
            x=households["year"], y=households[col], name=label, stackgroup="one", groupnorm="percent",
            mode="none", fillcolor=color, hovertemplate=f"{label}: %{{y:.2f}}%<extra></extra>"))
    annotations = []
    for year in [2013, 2023]:
        row = households[households["year"] == year]
        y_base = 0
        for col in cols:
            value = row[col].values[0]
            annotations.append(dict(
                x=year + (0.6 if year == 2013 else -0.4), y=y_base + value / 2, text=f"{value:.1f}%",
                showarrow=False, font=dict(color="white", size=14, family="Arial"),
                xanchor="center", yanchor="middle"))
            y_base += value
    fig.update_layout(
        height=600, plot_bgcolor="white", paper_bgcolor="white", margin=dict(l=40, r=40, t=40, b=60),
        xaxis=dict(title=None, tickmode="linear", dtick=1, tickfont=dict(size=12, color="black"),
                   showline=True, linecolor="black"),
        yaxis=dict(title="Share of Households (%)", range=[0, 100], ticksuffix="%", showline=True,
                   linecolor="black", tickfont=dict(size=12, color="black")),
        legend=dict(title="Monthly<br>Net Income (€)", title_font=dict(size=12, color="black", weight="bold"),
                    font=dict(size=12, color="black"), traceorder="normal",
                    yanchor="top", y=1, xanchor="left", x=1.01),
        hoverlabel=dict(font_size=14, font_family="Arial", font_color="black"),
        annotations=annotations)
    return fig


# ---- AFFORDABILITY TAB ----

BURDEN_SCALE = [[0.00, "#e0f3db"], [0.15, "#a8ddb5"], [0.30, "#41b17a"], [0.40, "#fecc5c"],
                [0.50, "#fd8d3c"], [0.60, "#f03b20"], [1.00, "#bd0026"]]

# Maximum monthly support for a single Bürgergeld recipient in Berlin: Regelsatz (563 €, unchanged
# 2024–2026) + AV-Wohnen gross cold rent cap for 1 person (449 €, since Oct 2023) + highest heating
# limit for 1 person (133 €).
BUERGERGELD = read_csv("income", "Buergergeld Max Transfer Estimate.csv").set_index("Component")["Amount (EUR)"]
INCOME_BUERGERGELD = BUERGERGELD["Total max estimate"]
TOTAL_PLRS = len(plr_geo)


def rent_burden_by_year():
    """Rent burden for a 1-room (50 m²) apartment vs monthly disposable income."""
    rents_by_year = (rents_BEZ.groupby("year")["median"].mean().reset_index()
                     .loc[lambda d: d["year"].between(2013, 2023)])
    return (
        income_persons.loc[lambda d: d["year"].between(2013, 2023)]
        .rename(columns={"monthly_disposable_income": "monthly_available_income"})
        .loc[:, ["year", "monthly_available_income"]]
        .merge(rents_by_year, on="year", how="inner")
        .assign(rent_1R=lambda d: (d["median"] * 50).round(0),
                rent_burden=lambda d: (d["rent_1R"] / d["monthly_available_income"] * 100).round(0))
    )


def rent_burden_by_plr():
    income_2023 = income_households.loc[income_households["year"] == 2023, "monthly_available_income"].values[0]
    return (
        rents_PLR.loc[rents_PLR["year"] == 2023, ["plr_id", "median"]]
        .assign(rent_1R=lambda d: d["median"] * 50,
                rent_burden_median_income=lambda d: d["rent_1R"] / income_2023,
                rent_burden_bg=lambda d: d["rent_1R"] / INCOME_BUERGERGELD)
        .merge(pd.DataFrame(plr_geo[["plr_id", "plr_name"]]), on="plr_id", how="left")
    )


def affordability_kpis(df):
    """Numbers quoted in the Affordability and Outlook text, so the copy always matches the maps."""
    def affordable(column, decimals):
        count = int((df[column] <= 0.30).sum())
        return {"affordable": str(count), "share": f"{count / TOTAL_PLRS * 100:.{decimals}f}%"}

    return {
        "median": affordable("rent_burden_median_income", 0),
        "bg": {
            **affordable("rent_burden_bg", 1),
            "allowance": f"{BUERGERGELD['Bürgergeld (cash)']:,.0f}",
            "rent_cap": f"{BUERGERGELD['Bruttokaltmiete cap (AV-Wohnen 1 person)']:,.0f}",
            "heating": f"{BUERGERGELD['Heating/utilities (high)']:,.0f}",
            "total": f"{INCOME_BUERGERGELD:,.0f}",
        },
    }


def afford_burden_line(df):
    first = df.loc[df["year"] == 2013, "rent_burden"].values[0]
    last = df.loc[df["year"] == 2023, "rent_burden"].values[0]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["year"], y=df["rent_1R"], name="1R Apartment Rent", fill="tonexty", fillcolor=ACCENT,
        mode="lines+markers", line=dict(color=ACCENT), marker=dict(size=6), yaxis="y1",
        hovertemplate="1R Apartment Rent<br>Year: %{x}<br>€ %{y:.0f}<extra></extra>"))
    fig.add_trace(go.Scatter(
        x=df["year"], y=df["monthly_available_income"], name="Available Income", fill="tonexty",
        mode="lines+markers", line=dict(color="#8F8F8F"), marker=dict(size=6), yaxis="y1",
        hovertemplate="Monthly Median Income<br>Year: %{x}<br>€ %{y:.0f}<extra></extra>"))
    fig.add_trace(go.Scatter(
        x=df["year"], y=df["rent_burden"], name="Rent Burden (%)", mode="lines+markers+text",
        line=dict(color=ACCENT), marker=dict(size=6, color=ACCENT),
        text=["" if y in [2013, 2023] else f"{int(v)}%" for y, v in zip(df["year"], df["rent_burden"])],
        textposition="top center", textfont=dict(color=ACCENT, size=13, family="Arial Black"), yaxis="y2",
        hovertemplate="Rent Burden<br>Year: %{x}<br>%{y:.0f}%<extra></extra>"))
    fig.update_layout(
        height=600, plot_bgcolor="white", paper_bgcolor="white",
        xaxis=dict(title=None, tickmode="linear", dtick=1, linecolor="black", showline=True,
                   tickfont=dict(size=14, color="black"), range=[2013, 2023]),
        yaxis=dict(title="€ per Month", showline=True, showgrid=False, linecolor="black",
                   tickfont=dict(color="black"), rangemode="tozero"),
        yaxis2=dict(title="Rent Burden (%)", overlaying="y", tickmode="auto", side="right", showline=True, showgrid=False,
                    linecolor="black", tickfont=dict(color="black"), range=[0, 45]),
        legend=dict(x=0.01, y=0.99, font=dict(size=16, color="black")),
        hoverlabel=dict(font_size=16, font_family="Arial", font_color="black"),
        margin=dict(l=60, r=60, t=40, b=60))
    for x, value in [(2013.3, first), (2022.7, last)]:
        fig.add_annotation(x=x, y=value, text=f"{int(value)}%", showarrow=False, xanchor="center",
                           yanchor="bottom", font=dict(color=ACCENT, size=13, family="Arial Black"), yref="y2")
    return fig


def afford_map(df, column):
    fig = px.choropleth_map(
        df, geojson=PLR_GEOJSON, locations="plr_id", featureidkey="properties.plr_id", color=column,
        color_continuous_scale=BURDEN_SCALE, range_color=[0, 0.6], center={"lat": 52.52, "lon": 13.405},
        zoom=10, map_style=MAP_STYLE, opacity=0.8, hover_name="plr_name")
    fig.update_traces(
        customdata=df[["rent_1R", column]],
        hovertext=df["plr_name"],
        hovertemplate="<b>%{hovertext}</b><br>Rent 1R Apt.: %{customdata[0]:.0f} €<br>"
                      "Rent Burden: %{customdata[1]:.1%}<extra></extra>",
        hoverlabel=dict(font_size=16, font_family="Inter"),
        marker_line_color="gray", marker_line_width=0.5)
    fig.update_layout(
        height=800, margin=dict(r=0, t=0, l=0, b=0),
        coloraxis_colorbar=dict(
            title="Rent Burden %", tickmode="array", tickvals=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
            ticktext=["0%", "10%", "20%", "30%", "40%", "50%", "60%"], tickfont=dict(size=14),
            len=0.3, y=0.05, x=0.01, xanchor="left", yanchor="bottom"))
    return fig


def afford_bins(burden, include_lowest, label_size):
    """Stacked column counting PLRs per rent-burden band, next to each map."""
    bins = [
        ("0–15%", burden <= 0.15, "#e0f3db"),
        ("15–30%", (burden > 0.15) & (burden < 0.30), "#a8ddb5"),
        ("30%", burden == 0.30, "#41b17a"),
        ("30–40%", (burden > 0.30) & (burden < 0.40), "#fecc5c"),
        ("40–50%", (burden >= 0.40) & (burden < 0.50), "#fd8d3c"),
        ("50–60%", (burden >= 0.50) & (burden < 0.60), "#f03b20"),
        ("60%+", burden >= 0.60, "#bd0026"),
    ]
    if not include_lowest:
        bins = bins[1:]
    bars, annotations, y_offset = [], [], 0
    for label, mask, color in bins:
        count = int(mask.sum())
        if count == 0:
            continue
        bars.append(go.Bar(x=["PLRs"], y=[count], marker=dict(color=color), width=1, name=label,
                           hovertemplate=f"{label}: {count} PLRs<extra></extra>", showlegend=False))
        annotations.append(dict(x="PLRs", y=y_offset + count / 2, text=str(count), showarrow=False,
                                font=dict(color="white", size=label_size), xanchor="center", yanchor="middle"))
        y_offset += count
    fig = go.Figure(data=bars)
    fig.update_layout(
        barmode="stack", height=800, margin=dict(t=0, b=0, l=0, r=0), plot_bgcolor="white",
        paper_bgcolor="white", annotations=annotations,
        xaxis=dict(showticklabels=False, showgrid=False, showline=False, zeroline=False, fixedrange=True),
        yaxis=dict(range=[0, y_offset], showticklabels=False, showgrid=False, showline=False,
                   zeroline=False, fixedrange=True))
    return fig


# ---- SOCIAL HOUSING TAB ----

ORANGE_SCALE = [[0.00, "#FFF5F0"], [0.25, "#FDBBA6"], [0.50, "#FC8A6A"], [0.75, "#F15842"], [1.00, "#D4583B"]]


def social_pgr_table():
    atlas = wohnatlas_2022.drop(columns=["pgr_name"]).copy()
    atlas["anteil_leistungsempfaenger"] = atlas["anteil_leistungsempfaenger"] / 100
    atlas["anteil_sozialwohng_2022"] = atlas["anteil_sozialwohng_2022"] / 100
    return pd.DataFrame(pgr_geo[["pgr_id", "pgr_name"]]).merge(
        atlas[["pgr_id", "anteil_leistungsempfaenger", "anteil_sozialwohng_2022"]], on="pgr_id", how="left")


def social_map(df, column, label, colorbar_title):
    fig = px.choropleth_map(
        df, geojson=PGR_GEOJSON, locations="pgr_id", featureidkey="properties.pgr_id", color=column,
        color_continuous_scale=ORANGE_SCALE, range_color=[0, df[column].max()], map_style=MAP_STYLE,
        center={"lat": 52.52, "lon": 13.405}, zoom=9, opacity=0.8, hover_name="pgr_name",
        hover_data={"pgr_id": False, column: ":.1%"}, labels={column: label})
    fig.update_layout(
        height=600, margin=dict(r=0, t=0, l=0, b=0),
        coloraxis_colorbar=dict(title=colorbar_title, tickformat=".0%", title_font=dict(size=12),
                                tickfont=dict(size=11), len=0.3, y=0.05, x=0.01,
                                xanchor="left", yanchor="bottom"))
    fig.update_traces(marker_line_color="gray", marker_line_width=0.5)
    return fig


def social_wbs():
    rename = {"1_person": "1 person", "2_person": "2 person", "3_person": "3 person",
              "4_person": "4 person", "5_person": "5 person", "5_or_more": "5 or more"}
    order = list(rename.values())
    wbs = wbs_berlin[wbs_berlin["year"].between(2015, 2023)].copy()
    wbs["housing_type"] = pd.Categorical(wbs["housing_type"].replace(rename), categories=order, ordered=True)
    pivot = wbs.pivot_table(index="year", columns="housing_type", values="amount",
                            aggfunc="sum", observed=False).fillna(0)[order]
    colors = ["#A33520", "#C84329", "#D4583B", "#EB9C7A", "#F3B39C", "#FCE0D9"]

    fig = go.Figure()
    for i, col in enumerate(pivot.columns):
        fig.add_trace(go.Bar(x=pivot.index, y=pivot[col], name=col, marker_color=colors[i], textposition="none"))
    for year, total in pivot.sum(axis=1).items():
        fig.add_annotation(x=year, y=total, text=f"{int(total):,}", showarrow=False, yanchor="bottom",
                           font=dict(size=13, color=ACCENT, family="Arial Black"))
    fig.update_layout(
        barmode="stack", height=600, plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=60, r=60, t=40, b=40),
        xaxis=dict(title="Year", tickmode="linear", dtick=1, showline=True, linecolor="black",
                   tickfont=dict(size=14, color="black")),
        yaxis=dict(title="Number of WBS Recipients", showline=True, linecolor="black", tickfont=dict(color="black")),
        legend=dict(title=None, font=dict(size=12, color="black"), traceorder="normal"))
    return fig


def social_subsidized():
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=subsidies["year"], y=subsidies["subsidized_housing"], marker_color=ACCENT,
        text=[f"{v:,}" for v in subsidies["subsidized_housing"]], textposition="outside",
        textfont=dict(color="black", size=12), name="New Subsidized Housing"))
    fig.update_layout(
        height=600, plot_bgcolor="white", paper_bgcolor="white", margin=dict(l=60, r=60, t=40, b=40),
        xaxis=dict(title="Year", tickmode="linear", dtick=1, showline=True, linecolor="black",
                   tickfont=dict(size=14, color="black")),
        yaxis=dict(title="Units with New Subsidy", showline=True, linecolor="black", tickfont=dict(color="black")),
        showlegend=False)
    return fig


def social_new_units():
    years = sh_subsidized_totals["year"]
    subsidised = sh_subsidized_totals["subsidised"]
    total_units = sh_subsidized_totals["total_units"]
    percent = (subsidised / total_units * 100).round(1)

    fig = go.Figure()
    fig.add_trace(go.Bar(x=years, y=subsidised, name="Subsidized Units", marker_color=ACCENT))
    fig.add_trace(go.Bar(x=years, y=total_units - subsidised, name="Non-Subsidized Units", marker_color="lightgrey"))
    for x, y, pct in zip(years, subsidised, percent):
        fig.add_annotation(x=x, y=y + 200, text=f"{pct}%", showarrow=False,
                           font=dict(color=ACCENT, size=13, family="Arial Black"), xanchor="center", yanchor="middle")
    for x, y in zip(years, total_units):
        fig.add_annotation(x=x, y=y + 200, text=f"{y:,}", showarrow=False,
                           font=dict(color="grey", size=12, family="Arial"), xanchor="center")
    fig.update_layout(
        barmode="stack", height=600, plot_bgcolor="white", paper_bgcolor="white",
        xaxis=dict(title="Year", tickmode="linear", dtick=1, linecolor="black", showline=True,
                   tickfont=dict(size=14, color="black")),
        yaxis=dict(title="New Housing Units", linecolor="black", showline=True, tickfont=dict(size=14, color="black")),
        legend=dict(x=0.01, y=0.99, font=dict(size=12, color="black")),
        margin=dict(l=60, r=60, t=40, b=40))
    return fig


# ---- OUTLOOK TAB ----

def outlook_your_rent():
    """Base map plus per-PLR 2023 median rents; app.js recomputes the burden in the browser
    whenever the income slider or apartment size changes."""
    rents = rents_PLR.loc[rents_PLR["year"] == 2023, ["plr_id", "median"]].dropna(subset=["median"])
    plrs = pd.DataFrame(plr_geo[["plr_id", "plr_name"]]).merge(rents, on="plr_id", how="inner")
    scale = [[0.00, "rgba(224,243,219,0.6)"], [0.15, "rgba(168,221,181,0.6)"], [0.30, "rgba(65,177,122,0.6)"],
             [0.40, "rgba(254,204,92,0.6)"], [0.50, "rgba(253,141,60,0.6)"], [0.60, "rgba(240,59,32,0.6)"],
             [1.00, "rgba(189,0,38,0.6)"]]
    fig = go.Figure(go.Choroplethmap(
        geojson=PLR_GEOJSON, locations=plrs["plr_id"], featureidkey="properties.plr_id",
        z=plrs["median"] * 50 / 1500, colorscale=scale, zmin=0, zmax=1.0,
        marker_line_color="gray", marker_line_width=0.5,
        colorbar=dict(title="Rent Burden %", tickformat=".0%", tickvals=[0.0, 0.3, 1], ticktext=["0%", "30%", "100%"],
                      len=0.3, thickness=15, y=0.05, x=0.01, xanchor="left", yanchor="bottom"),
        hoverinfo="text", name="Rent Burden",
        hoverlabel=dict(font_size=16, font_family="Arial", font_color="black")))
    fig.update_layout(map_style=MAP_STYLE, map_zoom=10, map_center={"lat": 52.52, "lon": 13.405},
                      height=900, margin=dict(l=0, r=0, t=0, b=0))
    return fig, {
        "names": plrs["plr_name"].tolist(),
        "median": plrs["median"].round(2).tolist(),
        "total_plrs": TOTAL_PLRS,
    }


# ---- BUILD ----

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print("Writing static data:")
    write_json("plr.geojson", PLR_GEOJSON)
    write_json("pgr.geojson", PGR_GEOJSON)

    write_json("intro.json", {"rent_map": fig_json(intro_rent_map(), "@plr")})

    districts = ["All Berlin"] + sorted(rents_BEZ["bez_name"].unique())
    increase_map, kpis = supply_increase_map()
    write_json("supply.json", {
        "rent_yoy": {d: fig_json(supply_rent_yoy(d)) for d in districts},
        "rent_yoy_options": districts,
        "increase_map": fig_json(increase_map, "@plr"),
        "kpis": kpis,
        "district_bars": fig_json(supply_district_bars()),
        "segmentation": fig_json(supply_segmentation()),
    })

    pop_options = sorted(net_migration["bez_name"].replace({"Berlin Insgesamt": "All Berlin"}).unique().tolist())
    write_json("demand.json", {
        "pop_migration": {o: fig_json(demand_pop_migration(o)) for o in pop_options},
        "pop_migration_options": pop_options,
        "income_line": fig_json(demand_income_line()),
        "income_stack": fig_json(demand_income_stack()),
    })

    by_plr = rent_burden_by_plr()
    kpis = affordability_kpis(by_plr)
    write_json("affordability.json", {
        "kpis": kpis,
        "burden_line": fig_json(afford_burden_line(rent_burden_by_year())),
        "median_map": fig_json(afford_map(by_plr, "rent_burden_median_income"), "@plr"),
        "median_bins": fig_json(afford_bins(by_plr["rent_burden_median_income"], True, 18)),
        "bg_map": fig_json(afford_map(by_plr, "rent_burden_bg"), "@plr"),
        "bg_bins": fig_json(afford_bins(by_plr["rent_burden_bg"], False, 20)),
    })

    pgr = social_pgr_table()
    write_json("social.json", {
        "welfare_map": fig_json(social_map(pgr, "anteil_leistungsempfaenger",
                                           "Social Welfare Receipients", "Social Welfare %"), "@pgr"),
        "wbs": fig_json(social_wbs()),
        "subsidized_map": fig_json(social_map(pgr, "anteil_sozialwohng_2022",
                                              "Subsidized Housing", "Subsidized Housing %"), "@pgr"),
        "subsidized_bars": fig_json(social_subsidized()),
        "new_units": fig_json(social_new_units()),
    })

    your_rent, your_rent_data = outlook_your_rent()
    write_json("outlook.json", {"your_rent": fig_json(your_rent, "@plr"), "your_rent_data": your_rent_data,
                                "kpis": kpis})


if __name__ == "__main__":
    main()
