#!/usr/bin/env python3
"""Precompute every chart of the Streamlit app into static JSON for the site in docs/.

The Streamlit app recomputed all figures on every start. This script runs the same
pandas/geopandas logic once and writes plain JSON files that docs/assets/app.js
renders with Plotly.js in the browser. Re-run it only when the data changes:

    pip install pandas geopandas plotly
    python scripts/build_static.py
"""
import json
import re
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "data" / "csv"
GEO = ROOT / "data" / "geo"
OUT = ROOT / "docs" / "data"

# Plotly's old "mapbox" traces load CARTO's retired raster CDN, which now only serves
# "API KEY REQUIRED" tiles. The MapLibre "map" traces use CARTO's vector styles
# instead, which work without a key.
MAP_STYLE = "carto-positron"
# The official boundaries, not simplified. 7 decimals (~1 cm) is the coarsest rounding that
# keeps every polygon valid; at 6 some boundaries start to self-intersect.
COORD_DECIMALS = 7

# Interface colours are plain CSS names here. app.js swaps each one for the page's
# standard or increased-contrast token (see TOKENS_BY_COLOR in app.js).
INK = "black"
INK_2 = "gray"
PAPER = "white"
GRID = "lightgray"
AXIS = "silver"
NEUTRAL = "dimgray"
ACCENT = "coral"
ACCENT_TEXT = "tomato"
MAP_LINE = "darkgray"
MAP_OUTLINE = "slategray"
ACCENT_WASH = "rgba(212,88,59,0.12)"
NEUTRAL_WASH = "rgba(142,142,147,0.12)"

# One-hue ordinal ramps, light to dark, for ordered bands. Checked with the dataviz
# validator (--ordinal) on the white card.
RAMP_5 = ["#F19D8B", "#E6735B", "#D04F30", "#AE3511", "#852604"]
RAMP_6 = ["#F19D8B", "#E97B64", "#DA5C40", "#C34322", "#A6310D", "#852604"]
RAMP_7 = ["#F39E8D", "#EC826C", "#E0664C", "#CF4E2F", "#B83A18", "#9E2D06", "#822300"]

# Plotly requires a colorscale; app.js replaces it with the named scale.
PLACEHOLDER_SCALE = [[0, "#ffffff"], [1, "#000000"]]
MAP_OPACITY = 0.85
OUTLINE_WIDTH = 1.2
AFFORDABLE = 0.30


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
BERLIN_BOUNDS = [round(float(v), 4) for v in plr_geo.total_bounds]
TOTAL_PLRS = len(plr_geo)


# ---- SERIALISATION ----

# Numbers are written European style: '.' between thousands, ',' before decimals. Python formats
# them the English way first; eu() swaps the two separators wherever they sit between digits.
_SEPARATOR = re.compile(r"(?<=\d)[.,](?=\d)")


def eu(text):
    return _SEPARATOR.sub(lambda m: "," if m.group() == "." else ".", text) if isinstance(text, str) else text



def fig_json(fig, geo=None, *, summary, scale=None, legend=None):
    """Figure as a plain dict, plus the descriptive text and colour scale the page shows
    with it. Map traces get a "@plr"/"@pgr" placeholder instead of the GeoJSON (shared
    files loaded once in the browser); app.js applies the theme to every chart."""
    d = json.loads(fig.to_json())
    d["layout"].pop("template", None)
    for trace in d["data"] + [t for frame in d.get("frames", []) for t in frame.get("data", [])]:
        if "geojson" in trace:
            trace["geojson"] = geo
        for key in ("name", "hovertemplate"):
            if key in trace:
                trace[key] = eu(trace[key])
        if isinstance(trace.get("text"), list):
            trace["text"] = [eu(t) for t in trace["text"]]
    for annotation in d["layout"].get("annotations", []):
        annotation["text"] = eu(annotation.get("text"))
    d["summary"] = eu(summary)
    if scale:
        d["scale"] = scale
    if legend:
        legend = {**legend, "ticks": [{**tick, "t": eu(tick["t"])} for tick in legend["ticks"]]}
        if "note" in legend:
            legend["note"] = eu(legend["note"])
        d["legend"] = legend
    if geo:
        d["fit"] = BERLIN_BOUNDS
    return d


def write_json(name, payload):
    path = OUT / name
    path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"  {path.relative_to(ROOT)}  {path.stat().st_size / 1024:,.0f} KB")






# ---- SHARED CHART ANATOMY ----

# The top margin leaves room for the chart toolbar, so it never covers the plot
MARGIN = dict(l=8, r=8, t=44, b=28)
# Legends sit at the foot of the chart. Anchored to the container, they push the plot up
# instead of overlapping the axis labels.
LEGEND = dict(orientation="h", x=0, xanchor="left", y=0, yanchor="bottom", yref="container", traceorder="normal")


# Value axes write numbers in full with the European thousands point (2.500, 180.000, 3.500.000),
# not Plotly's English "k" and "M" abbreviations. Year axes keep plain years (2013).
VALUE_TICKS = dict(separatethousands=True, exponentformat="none")


def x_years(dtick=1, **kwargs):
    return {**dict(tickmode="linear", dtick=dtick, showgrid=False, showline=True, linecolor=AXIS, ticks="",
                   zeroline=False), **kwargs}


def y_values(**kwargs):
    """Value axis on the trailing side, so the plot keeps a clean leading edge."""
    return {**dict(side="right", showgrid=True, gridcolor=GRID, gridwidth=1, showline=False, ticks="", zeroline=False,
                   **VALUE_TICKS),
            **kwargs}


# Double-axis charts: an axis line on each side, as on the original charts
SIDE_AXIS = dict(showgrid=False, showline=True, linecolor=AXIS, ticks="", zeroline=False, **VALUE_TICKS)


def value_chip(x, y, text, **kwargs):
    """Value label on a dark chip, as on the original charts."""
    return dict(x=x, y=y, text=text, showarrow=False, bgcolor=INK, borderpad=4, font=dict(color=PAPER, size=14), **kwargs)


def end_label(x, y, text, yref="y", xanchor="right", yshift=10):
    return dict(x=x, y=y, yref=yref, text=f"<b>{text}</b>", showarrow=False, xanchor=xanchor, yanchor="bottom",
                yshift=yshift, font=dict(size=13, color=INK))


def choropleth(df, id_col, geojson, z, names, *, hover, zmin, zmax, customdata=None, highlight=None):
    highlight = np.zeros(len(df), dtype=bool) if highlight is None else np.asarray(highlight)
    fig = go.Figure(go.Choroplethmap(
        geojson=geojson, locations=df[id_col], featureidkey=f"properties.{id_col}", z=z,
        zmin=zmin, zmax=zmax, colorscale=PLACEHOLDER_SCALE, showscale=False,
        marker=dict(opacity=MAP_OPACITY, line=dict(color=[MAP_OUTLINE if h else MAP_LINE for h in highlight],
                                                   width=[OUTLINE_WIDTH if h else 0.5 for h in highlight])),
        customdata=customdata, hovertext=names, hovertemplate=hover))
    fig.update_layout(map=dict(style=MAP_STYLE, center=dict(lat=52.5, lon=13.405), zoom=9.6),
                      margin=dict(l=0, r=0, t=0, b=0))
    return fig


# ---- INTRO TAB ----

def intro_rent_map():
    rents = rents_PLR[rents_PLR["year"].between(2013, 2023) & rents_PLR["plr_id"].isin(plr_geo["plr_id"])]
    years = sorted(rents["year"].unique())
    pivot = rents.pivot(index="plr_id", columns="year", values="median")
    names = rents.drop_duplicates("plr_id").set_index("plr_id")["plr_name"].reindex(pivot.index)
    vmin, vmax = rents["median"].min(), rents["median"].max()
    df = pivot.reset_index()

    fig = choropleth(df, "plr_id", PLR_GEOJSON, df[years[0]], names.tolist(),
                     hover="<b>%{hovertext}</b><br>%{z:.2f} €/m²<extra></extra>", zmin=vmin, zmax=vmax)
    fig.frames = [go.Frame(name=str(y), data=[go.Choroplethmap(z=df[y])], traces=[0]) for y in years]

    ticks = [{"v": v, "t": str(v)} for v in range(5, int(vmax) + 1, 5)]
    return fig_json(
        fig, "@plr", scale="heat",
        summary=f"Median asking rent per planning area, from {vmin:.2f} to {vmax:.2f} €/m² across all years.",
        legend={"title": "Median rent (€/m²)", "min": float(vmin), "max": float(vmax), "ticks": ticks,
                "note": "Blank areas have no rent data for that year."})


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
    span = filtered.max() - filtered.min()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=yoy.index, y=yoy.values, name="Yearly Increase (%)", yaxis="y", offsetgroup=0,
        marker=dict(color=ACCENT, cornerradius=3), text=[f"{v:.2f}%" if pd.notna(v) else "" for v in yoy],
        textposition="outside", constraintext="none", cliponaxis=False,
        textfont=dict(color=ACCENT_TEXT, size=13, weight="bold"),
        hovertemplate="Yearly increase: %{y:.2f}%<extra></extra>"))
    fig.add_trace(go.Scatter(
        x=filtered.index, y=filtered.values, name="Median Rent (€/m²)", mode="lines+markers", yaxis="y2",
        line=dict(color=INK, width=2.5), marker=dict(size=8, color=INK, line=dict(color=PAPER, width=2)),
        hovertemplate="Median rent: %{y:.2f} €/m²<extra></extra>"))
    fig.add_annotation(**value_chip(filtered.index[0], filtered.iloc[0], f"{filtered.iloc[0]:.2f} €/m²", yref="y2",
                                    xanchor="left", yanchor="top", xshift=-14, yshift=-10))
    fig.add_annotation(**value_chip(filtered.index[-1], filtered.iloc[-1], f"{filtered.iloc[-1]:.2f} €/m²", yref="y2",
                                    xanchor="right", yanchor="middle", xshift=-12))
    fig.add_shape(type="line", x0=2012.6, x1=2023.6, y0=0, y1=0, xref="x", yref="y",
                  line=dict(color=INK, width=1.5), layer="above")
    fig.update_layout(
        xaxis=x_years(tick0=int(filtered.index[0])),
        yaxis=dict(SIDE_AXIS, title=dict(text="Yearly Increase (%)", font=dict(color=INK)),
                   range=[min(yoy.min(), 0) * 1.3 - 1, yoy.max() * 1.4]),
        yaxis2=dict(SIDE_AXIS, title=dict(text="Median Rent (€/m²)", font=dict(color=INK)), overlaying="y", tickmode="auto",
                    side="right", range=[filtered.min() - 0.2 * span, filtered.max() + 0.06 * span]),
        legend=LEGEND, bargap=0.3, margin=MARGIN, hovermode="x unified")
    return fig


def rent_yoy_summary(district):
    filtered = rent_series(district)
    first, last = filtered.iloc[0], filtered.iloc[-1]
    return f"{district}: {first:.2f} €/m² in {filtered.index[0]}, {last:.2f} €/m² in {filtered.index[-1]}."




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
        "max": {"value": eu(f"{max_plr['pct_increase']:.1f}%").replace("-", "−"), "name": max_plr["plr_name"]},
        "min": {"value": eu(f"{min_plr['pct_increase']:.1f}%").replace("-", "−"), "name": min_plr["plr_name"]},
    }
    doubled = gdf["pct_increase"] >= 100

    fig = choropleth(
        gdf, "plr_id", PLR_GEOJSON, gdf["pct_increase"], gdf["plr_name"].tolist(), zmin=-40, zmax=300,
        customdata=gdf[["rent_2013", "rent_2023"]].to_numpy(), highlight=doubled,
        hover="<b>%{hovertext}</b><br>Rent 2013: %{customdata[0]:.2f} €/m²<br>Rent 2023: %{customdata[1]:.2f} €/m²"
              "<br>Increase: %{z:.1f}%<extra></extra>")
    legend = {"title": "Rent change 2013–2023", "min": -40, "max": 300,
              "ticks": [{"v": -40, "t": "−40%"}, {"v": 0, "t": "0%"}, {"v": 100, "t": "100%", "strong": True},
                        {"v": 200, "t": "200%"}, {"v": 300, "t": "300%"}],
              "note": "Outlined areas at least doubled. Blank areas have no rent data."}
    summary = (f"{int(doubled.sum())} of {int(gdf['pct_increase'].notna().sum())} planning areas with data at least "
               f"doubled, from {min_plr['pct_increase']:.1f}% to {max_plr['pct_increase']:.1f}%.").replace("-", "−")
    return fig_json(fig, "@plr", scale="change", summary=summary, legend=legend), kpis


def supply_district_bars():
    rents = rents_BEZ[rents_BEZ["year"].isin([2013, 2023])].copy()
    rents["year"] = rents["year"].astype(str)
    pivot = rents.pivot(index="bez_name", columns="year", values="median").reset_index()
    pivot["pct_increase"] = ((pivot["2023"] - pivot["2013"]) / pivot["2013"] * 100).round(1)
    pivot["label"] = pivot["pct_increase"].astype(str) + "% increase"
    pivot = pivot.sort_values("2023", ascending=False)

    fig = go.Figure()
    fig.add_trace(go.Bar(y=pivot["bez_name"], x=pivot["2013"], name="2013", orientation="h",
                         marker=dict(color=NEUTRAL, cornerradius=3),
                         hovertemplate="2013: %{x:.2f} €/m²<extra></extra>"))
    fig.add_trace(go.Bar(y=pivot["bez_name"], x=pivot["2023"], name="2023", orientation="h",
                         marker=dict(color=ACCENT, cornerradius=3), text=pivot["label"], textposition="outside",
                         constraintext="none", cliponaxis=False, textfont=dict(size=12, color=INK_2),
                         hovertemplate="2023: %{x:.2f} €/m²<extra></extra>"))
    fig.update_layout(
        yaxis=dict(autorange="reversed", showgrid=False, showline=False, ticks="", ticklabelstandoff=6),
        xaxis=dict(showgrid=True, gridcolor=GRID, zeroline=False, showline=False, ticks="",
                   range=[0, max(pivot["2023"]) * 1.32], fixedrange=True, title="Median rent (€/m²)"),
        barmode="group", bargap=0.3, bargroupgap=0.08, legend=LEGEND, margin=MARGIN, hovermode="y unified")
    top, low = pivot.iloc[0], pivot.iloc[-1]
    return fig_json(fig, summary=f"Highest in 2023: {top['bez_name']}, {top['2023']:.2f} €/m². "
                                 f"Lowest: {low['bez_name']}, {low['2023']:.2f} €/m².")


def supply_segmentation():
    structure = rent_structure.copy()
    structure.loc[structure["Bezirk"] == "Berlin insgesamt", "Bezirk"] = "Total Berlin"
    main = structure[structure["Bezirk"] != "Total Berlin"]
    total = structure[structure["Bezirk"] == "Total Berlin"]
    df = pd.concat([main.sort_values(by="≥18 EUR/m²", ascending=False), total], ignore_index=True)

    # Expensive → affordable, darkest first
    price_columns = list(reversed([c for c in rent_structure.columns if c != "Bezirk"]))
    colors = list(reversed(RAMP_7))
    order = df["Bezirk"].tolist()
    order = order[:-1][::-1] + [order[-1]]

    fig = go.Figure()
    offsets = {bez: 0 for bez in df["Bezirk"]}
    annotations = []
    for i, col in enumerate(price_columns):
        for bez, value in zip(df["Bezirk"], df[col]):
            if bez == "Total Berlin":
                # Percentage labels only on the "Total Berlin" bar
                annotations.append(dict(x=value / 2 + offsets[bez], y=bez, text=f"{value}%", showarrow=False,
                                        name=f"on:{colors[i]}", font=dict(size=12),
                                        xanchor="center", yanchor="middle"))
            offsets[bez] += value
        fig.add_trace(go.Bar(y=df["Bezirk"], x=df[col], name=col.replace(" EUR/m²", " €/m²"), orientation="h",
                             marker=dict(color=colors[i], line=dict(color=PAPER, width=2)), textposition="none",
                             hovertemplate=f"{col.replace(' EUR/m²', ' €/m²')}: %{{x}}%<extra></extra>"))
    fig.update_layout(
        barmode="stack", bargap=0.3, annotations=annotations,
        xaxis=dict(ticksuffix="%", range=[0, 100], showgrid=True, gridcolor=GRID, zeroline=False, showline=False,
                   ticks=""),
        yaxis=dict(type="category", categoryorder="array", categoryarray=order, showgrid=False, showline=False,
                   ticks="", ticklabelstandoff=6),
        margin=dict(MARGIN, r=20), hovermode="y unified",
        legend=dict(LEGEND, title=dict(text="Monthly cold rent", side="top")))
    t = df[df["Bezirk"] == "Total Berlin"].iloc[0]
    return fig_json(fig, summary=f"Across Berlin in 2023, {t['≥18 EUR/m²']}% of listings asked 18 €/m² or more "
                                 f"and {t['<8 EUR/m²']}% asked under 8 €/m².")


# ---- DEMAND TAB ----

def demand_growth(option):
    if option == "All Berlin":
        pop = pop_BEZ.groupby("year")["population"].sum().reset_index()
        mig = (net_migration[net_migration["bez_name"] != "Berlin Insgesamt"]
               .groupby("year")["net_migration"].sum().reset_index())
    else:
        pop = pop_BEZ[pop_BEZ["bez_name"] == option][["year", "population"]]
        mig = net_migration[net_migration["bez_name"] == option][["year", "net_migration"]]
    return pop.merge(mig, on="year", how="inner").sort_values("year")


def demand_pop_migration(option):
    growth = demand_growth(option)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=growth["year"], y=growth["population"], name="Total Population", mode="lines+markers", yaxis="y",
        line=dict(color=INK, width=2), marker=dict(size=8, color=INK, line=dict(color=PAPER, width=2)),
        hovertemplate="Total population: %{y:,}<extra></extra>"))
    fig.add_trace(go.Bar(
        x=growth["year"], y=growth["net_migration"], base=0, name="Net Migration", yaxis="y2", width=0.5,
        marker=dict(color=ACCENT, cornerradius=3), text=[f"{v:,}" for v in growth["net_migration"]],
        textposition="outside", constraintext="none", cliponaxis=False,
        textfont=dict(color=ACCENT_TEXT, size=13, weight="bold"), hovertemplate="Net migration: %{y:,}<extra></extra>"))
    for i, anchor, shift in ([(0, "left", -10), (-1, "right", 10)] if len(growth) > 1 else [(0, "left", -10)]):
        fig.add_annotation(**value_chip(growth["year"].iloc[i], growth["population"].iloc[i] * 0.98,
                                        f"{growth['population'].iloc[i]:,}", xanchor=anchor, xshift=shift, yanchor="top"))
    fig.add_shape(type="line", xref="paper", yref="y2", x0=0, x1=1, y0=0, y1=0, line=dict(color=INK, width=1.5))
    # The migration axis stays fixed at 0–180,000 so districts compare directly with each other
    fig.update_layout(
        xaxis=x_years(tick0=int(growth["year"].iloc[0])),
        yaxis=dict(SIDE_AXIS, title=dict(text="Total Population", font=dict(color=INK)), rangemode="tozero"),
        yaxis2=dict(SIDE_AXIS, title=dict(text="Net Migration", font=dict(color=INK)), range=[0, 180000], overlaying="y",
                    tickmode="auto", side="right"),
        legend=LEGEND, margin=MARGIN, hovermode="x unified")
    return fig


def pop_summary(option):
    growth = demand_growth(option)
    first, last = growth.iloc[0], growth.iloc[-1]
    return f"{option}: population {first['population']:,} in {first['year']}, {last['population']:,} in {last['year']}."




def demand_income_line():
    first_year, first_value = income_persons["year"].iloc[0], income_persons["monthly_disposable_income"].iloc[0]
    last_year, last_value = income_persons["year"].iloc[-1], income_persons["monthly_disposable_income"].iloc[-1]
    fig = go.Figure(go.Scatter(
        x=income_persons["year"], y=income_persons["monthly_disposable_income"], mode="lines+markers",
        name="Monthly Net Income", line=dict(color=INK, width=2), marker=dict(size=8, color=INK, line=dict(color=PAPER, width=2)),
        hovertemplate="%{x}: %{y:.2f} €<extra></extra>"))
    fig.update_layout(margin=MARGIN, xaxis=x_years(dtick=4, tick0=int(first_year)), yaxis=y_values(rangemode="tozero", ticksuffix=" €"),
                      annotations=[end_label(last_year, last_value, f"{last_value:,.2f} €")], hovermode="closest")
    return fig_json(fig, summary=f"{first_value:,.2f} € per month in {first_year}, {last_value:,.2f} € in {last_year}. "
                                 "Not adjusted for inflation.")


def demand_income_stack():
    cols = ["%_under_900", "%_900_1500", "%_1500_2600", "%_2600_4500", "%_over_4500"]
    labels = ["Under 900", "900–1,500", "1,500–2,600", "2,600–4,500", "Over 4,500"]
    households = income_households.copy()
    for col in cols:
        households[col] = comma_float(households[col])

    fig = go.Figure()
    for col, label, color in zip(cols, labels, RAMP_5):
        fig.add_trace(go.Scatter(
            x=households["year"], y=households[col], name=label, stackgroup="one", groupnorm="percent",
            mode="lines", line=dict(color=PAPER, width=2), fillcolor=color,
            hovertemplate=f"{label}: %{{y:.2f}}%<extra></extra>"))
    annotations = []
    for year in [2013, 2023]:
        row = households[households["year"] == year]
        y_base = 0
        for col, color in zip(cols, RAMP_5):
            value = row[col].values[0]
            annotations.append(dict(
                x=year, y=y_base + value / 2, text=f"{value:.1f}%", showarrow=False, name=f"on:{color}",
                font=dict(size=12, weight="bold"), xanchor="left" if year == 2013 else "right", xshift=6 if year == 2013 else -6,
                yanchor="middle"))
            y_base += value
    fig.update_layout(
        margin=dict(MARGIN, l=20), xaxis=x_years(tick0=2013), hovermode="x unified",
        yaxis=y_values(range=[0, 100], ticksuffix="%"), annotations=annotations,
        legend=dict(LEGEND, title=dict(text="Monthly net income (€)", side="top")))
    first = households[households["year"] == 2013].iloc[0]
    last = households[households["year"] == 2023].iloc[0]
    return fig_json(fig, summary=f"Households with over 4,500 € per month: {first['%_over_4500']:.1f}% in 2013, "
                                 f"{last['%_over_4500']:.1f}% in 2023. Under 900 €: {first['%_under_900']:.1f}% and "
                                 f"{last['%_under_900']:.1f}%.")


# ---- AFFORDABILITY TAB ----

# Maximum monthly support for a single Bürgergeld recipient in Berlin: Regelsatz (563 €, unchanged
# 2024–2026) + AV-Wohnen gross cold rent cap for 1 person (449 €, since Oct 2023) + highest heating
# limit for 1 person (133 €).
BUERGERGELD = read_csv("income", "Buergergeld Max Transfer Estimate.csv").set_index("Component")["Amount (EUR)"]
INCOME_BUERGERGELD = BUERGERGELD["Total max estimate"]

BURDEN_LEGEND = {
    "title": "Rent burden", "min": 0, "max": 0.6,
    "ticks": [{"v": 0, "t": "0%"}, {"v": 0.15, "t": "15%"}, {"v": 0.3, "t": "30%", "strong": True},
              {"v": 0.45, "t": "45%"}, {"v": 0.6, "t": "60%+"}],
    "note": "Outlined areas are affordable: 30% or less. Blank areas have no rent data.",
}


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
        count = int((df[column] <= AFFORDABLE).sum())
        return {"affordable": str(count), "share": eu(f"{count / TOTAL_PLRS * 100:.{decimals}f}%")}

    return {
        "median": affordable("rent_burden_median_income", 0),
        "bg": {
            **affordable("rent_burden_bg", 1),
            "allowance": eu(f"{BUERGERGELD['Bürgergeld (cash)']:,.0f}"),
            "rent_cap": eu(f"{BUERGERGELD['Bruttokaltmiete cap (AV-Wohnen 1 person)']:,.0f}"),
            "heating": eu(f"{BUERGERGELD['Heating/utilities (high)']:,.0f}"),
            "total": eu(f"{INCOME_BUERGERGELD:,.0f}"),
        },
    }


def afford_burden_line(df):
    """Rent and income in € on the left axis, rent burden in % on the right, as on the original chart.
    The € axis runs to 3,000 so the burden line keeps to the top of the chart, clear of the income line."""
    first = df.loc[df["year"] == 2013, "rent_burden"].values[0]
    last = df.loc[df["year"] == 2023, "rent_burden"].values[0]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["year"], y=df["rent_1R"], name="1R Apartment Rent", mode="lines+markers", yaxis="y", fill="tozeroy",
        fillcolor=ACCENT_WASH, line=dict(color=ACCENT, width=2),
        marker=dict(size=8, color=ACCENT, line=dict(color=PAPER, width=2)),
        hovertemplate="1R apartment rent: %{y:,.0f} €<extra></extra>"))
    fig.add_trace(go.Scatter(
        x=df["year"], y=df["monthly_available_income"], name="Available Income", mode="lines+markers", yaxis="y",
        fill="tonexty", fillcolor=NEUTRAL_WASH, line=dict(color=NEUTRAL, width=2),
        marker=dict(size=8, color=NEUTRAL, line=dict(color=PAPER, width=2)),
        hovertemplate="Median income: %{y:,.0f} €<extra></extra>"))
    fig.add_trace(go.Scatter(
        x=df["year"], y=df["rent_burden"], name="Rent Burden (%)", mode="lines+markers", yaxis="y2",
        line=dict(color=INK, width=2.5), marker=dict(size=8, color=INK, line=dict(color=PAPER, width=2)),
        hovertemplate="Rent burden: %{y:.0f}%<extra></extra>"))
    fig.add_shape(type="line", xref="paper", x0=0, x1=1, yref="y2", y0=30, y1=30,
                  line=dict(color=INK_2, width=1, dash="dash"))
    fig.add_annotation(text="30% affordability threshold", xref="paper", x=0, xanchor="left", yref="y2", y=30,
                       yanchor="bottom", showarrow=False, font=dict(size=12, color=INK_2))
    fig.add_annotation(**value_chip(2013, first, f"{int(first)}%", yref="y2", xanchor="left", yanchor="top",
                                    xshift=-14, yshift=-10))
    fig.add_annotation(**value_chip(2023, last, f"{int(last)}%", yref="y2", xanchor="right", yanchor="middle",
                                    xshift=-12))
    fig.update_layout(
        xaxis=x_years(tick0=2013, range=[2012.6, 2023.4]),
        yaxis=dict(SIDE_AXIS, title=dict(text="€ per month", font=dict(color=INK)), range=[0, 3000]),
        yaxis2=dict(SIDE_AXIS, title=dict(text="Rent burden (%)", font=dict(color=INK)), range=[0, 40],
                    overlaying="y", side="right", tickmode="auto"),
        legend=LEGEND, margin=MARGIN, hovermode="x unified")
    return fig_json(fig, summary=f"Rent for a 50 m² apartment took {int(first)}% of monthly income in 2013 "
                                 f"and {int(last)}% in 2023. The threshold is 30%.")


def afford_map(df, column, who):
    highlight = df[column] <= AFFORDABLE
    fig = choropleth(
        df, "plr_id", PLR_GEOJSON, df[column], df["plr_name"].tolist(), zmin=0, zmax=0.6,
        customdata=df[["rent_1R"]].to_numpy(), highlight=highlight,
        hover="<b>%{hovertext}</b><br>Rent 1R Apt.: %{customdata[0]:.0f} €<br>Rent Burden: %{z:.1%}<extra></extra>")
    return fig_json(fig, "@plr", scale="burden", legend=BURDEN_LEGEND,
                    summary=f"For {who}, {int(highlight.sum())} of {int(df[column].notna().sum())} planning areas with "
                            f"rent data are at or below 30%, out of {TOTAL_PLRS} in total.")


def afford_bins(burden, include_lowest, who):
    """Planning areas per rent-burden band, directly labelled, beside each map."""
    bins = [
        ("0–15%", burden <= 0.15, 0.08),
        ("15–30%", (burden > 0.15) & (burden < 0.30), 0.23),
        ("30%", burden == 0.30, 0.29),
        ("30–40%", (burden > 0.30) & (burden < 0.40), 0.35),
        ("40–50%", (burden >= 0.40) & (burden < 0.50), 0.45),
        ("50–60%", (burden >= 0.50) & (burden < 0.60), 0.55),
        ("60%+", burden >= 0.60, 0.6),
    ]
    if not include_lowest:
        bins = bins[1:]
    rows = [(label, int(mask.sum()), mid) for label, mask, mid in bins if mask.sum() > 0]
    fig = go.Figure(go.Bar(
        y=[r[0] for r in rows], x=[r[1] for r in rows], orientation="h", width=0.68, text=[str(r[1]) for r in rows],
        textposition="outside", constraintext="none", cliponaxis=False, textfont=dict(size=13, color=INK),
        marker=dict(color=[r[2] for r in rows], colorscale=PLACEHOLDER_SCALE, cmin=0, cmax=0.6, cornerradius=3),
        hovertemplate="%{y}: %{x} PLRs<extra></extra>"))
    fig.update_layout(
        margin=dict(l=8, r=8, t=4, b=4), hovermode="closest",
        xaxis=dict(visible=False, fixedrange=True, range=[0, max(r[1] for r in rows) * 1.22]),
        yaxis=dict(autorange="reversed", showgrid=False, showline=False, ticks="", fixedrange=True,
                   ticklabelstandoff=6))
    affordable = sum(r[1] for r in rows if r[0] in ("0–15%", "15–30%", "30%"))
    return fig_json(fig, scale="burden", summary=f"For {who}: {affordable} areas at or below 30%, "
                                                 f"{sum(r[1] for r in rows) - affordable} above.")






# ---- SOCIAL HOUSING TAB ----

def social_pgr_table():
    atlas = wohnatlas_2022.drop(columns=["pgr_name"]).copy()
    atlas["anteil_leistungsempfaenger"] = atlas["anteil_leistungsempfaenger"] / 100
    atlas["anteil_sozialwohng_2022"] = atlas["anteil_sozialwohng_2022"] / 100
    return pd.DataFrame(pgr_geo[["pgr_id", "pgr_name"]]).merge(
        atlas[["pgr_id", "anteil_leistungsempfaenger", "anteil_sozialwohng_2022"]], on="pgr_id", how="left")


def social_map(df, column, label):
    top = float(df[column].max())
    step = 0.05 if top < 0.25 else 0.1
    ticks = [{"v": round(v, 2), "t": f"{v * 100:.0f}%"} for v in np.arange(0, top + 1e-9, step)]
    fig = choropleth(df, "pgr_id", PGR_GEOJSON, df[column], df["pgr_name"].tolist(), zmin=0, zmax=top,
                     hover=f"<b>%{{hovertext}}</b><br>{label}: %{{z:.1%}}<extra></extra>")
    named = df.dropna(subset=[column])
    high, low = named.loc[named[column].idxmax()], named.loc[named[column].idxmin()]
    return fig_json(fig, "@pgr", scale="heat",
                    summary=f"Highest: {high['pgr_name']}, {high[column]:.1%}. Lowest: {low['pgr_name']}, {low[column]:.1%}.",
                    legend={"title": label, "min": 0, "max": top, "ticks": ticks})


def social_wbs():
    rename = {"1_person": "1 person", "2_person": "2 person", "3_person": "3 person",
              "4_person": "4 person", "5_person": "5 person", "5_or_more": "5 or more"}
    order = list(rename.values())
    wbs = wbs_berlin[wbs_berlin["year"].between(2015, 2023)].copy()
    wbs["housing_type"] = pd.Categorical(wbs["housing_type"].replace(rename), categories=order, ordered=True)
    pivot = wbs.pivot_table(index="year", columns="housing_type", values="amount",
                            aggfunc="sum", observed=False).fillna(0)[order]
    colors = list(reversed(RAMP_6))

    fig = go.Figure()
    for i, col in enumerate(pivot.columns):
        fig.add_trace(go.Bar(x=pivot.index, y=pivot[col], name=col, width=0.5,
                             marker=dict(color=colors[i], line=dict(color=PAPER, width=2)), textposition="none",
                             hovertemplate=f"{col}: %{{y:,}}<extra></extra>"))
    totals = pivot.sum(axis=1)
    annotations = [dict(x=year, y=total, text=f"{int(total):,}", showarrow=False, yanchor="bottom", name="thin",
                        font=dict(size=12, color=INK_2)) for year, total in totals.items()]
    fig.update_layout(barmode="stack", margin=MARGIN, legend=LEGEND, xaxis=x_years(tick0=2015), yaxis=y_values(),
                      hovermode="x unified", annotations=annotations)
    return fig_json(fig, summary=f"{int(totals.iloc[0]):,} recipients in {totals.index[0]}, "
                                 f"{int(totals.iloc[-1]):,} in {totals.index[-1]}.")


def social_subsidized():
    fig = go.Figure(go.Bar(
        x=subsidies["year"], y=subsidies["subsidized_housing"], width=0.5, name="New Subsidized Housing",
        marker=dict(color=ACCENT, cornerradius=3), text=[f"{v:,}" for v in subsidies["subsidized_housing"]],
        textposition="outside", constraintext="none", cliponaxis=False, textfont=dict(size=12, color=INK_2),
        hovertemplate="%{x}: %{y:,} units<extra></extra>"))
    fig.update_layout(margin=MARGIN, xaxis=x_years(tick0=2015), yaxis=y_values(), showlegend=False,
                      hovermode="closest")
    first, last = subsidies.iloc[0], subsidies.iloc[-1]
    return fig_json(fig, summary=f"{first['subsidized_housing']:,} units in {first['year']}, "
                                 f"{last['subsidized_housing']:,} in {last['year']}.")


def social_new_units():
    data = sh_subsidized_totals.sort_values("year")
    years = data["year"]
    subsidised = data["subsidised"]
    total_units = data["total_units"]
    percent = (subsidised / total_units * 100).round(1)

    fig = go.Figure()
    fig.add_trace(go.Bar(x=years, y=subsidised, name="Subsidized Units", width=0.5,
                         marker=dict(color=ACCENT, line=dict(color=PAPER, width=2)),
                         hovertemplate="Subsidized: %{y:,}<extra></extra>"))
    fig.add_trace(go.Bar(x=years, y=total_units - subsidised, name="Non-Subsidized Units", width=0.5,
                         marker=dict(color=NEUTRAL, line=dict(color=PAPER, width=2)),
                         hovertemplate="Non-subsidized: %{y:,}<extra></extra>"))
    # The share sits inside the subsidized segment, the total above the column
    annotations = [dict(x=x, y=y / 2, text=f"{pct}%", showarrow=False, name=f"on:{'#D4583B'}", font=dict(size=12),
                        xanchor="center", yanchor="middle") for x, y, pct in zip(years, subsidised, percent)]
    annotations += [dict(x=x, y=y, text=f"{y:,}", showarrow=False, yanchor="bottom", xanchor="center", name="thin",
                         font=dict(size=12, color=INK_2)) for x, y in zip(years, total_units)]
    fig.update_layout(barmode="stack", margin=MARGIN, legend=LEGEND, xaxis=x_years(tick0=2017), yaxis=y_values(),
                      hovermode="x unified", annotations=annotations)
    return fig_json(fig, summary=f"In {years.iloc[-1]}, {percent.iloc[-1]}% of {total_units.iloc[-1]:,} new units were "
                                 f"subsidized. In {years.iloc[0]}: {percent.iloc[0]}% of {total_units.iloc[0]:,}.")


# ---- OUTLOOK TAB ----

def outlook_your_rent():
    """Base map plus per-PLR 2023 median rents; app.js recomputes the burden in the browser
    whenever the income slider or apartment size changes."""
    rents = rents_PLR.loc[rents_PLR["year"] == 2023, ["plr_id", "median"]].dropna(subset=["median"])
    plrs = pd.DataFrame(plr_geo[["plr_id", "plr_name"]]).merge(rents, on="plr_id", how="inner")
    z = plrs["median"] * 50 / 1500
    fig = choropleth(plrs, "plr_id", PLR_GEOJSON, z, None, zmin=0, zmax=0.6, highlight=z <= AFFORDABLE, hover=None)
    fig.update_traces(hoverinfo="text", name="Rent Burden")
    return (
        fig_json(fig, "@plr", scale="burden", legend=BURDEN_LEGEND, summary=""),
        {"names": plrs["plr_name"].tolist(), "median": plrs["median"].round(2).tolist(), "total_plrs": TOTAL_PLRS},
    )


# ---- BUILD ----

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print("Writing static data:")
    write_json("plr.geojson", PLR_GEOJSON)
    write_json("pgr.geojson", PGR_GEOJSON)

    write_json("intro.json", {"rent_map": intro_rent_map()})

    districts = ["All Berlin"] + sorted(rents_BEZ["bez_name"].unique())
    increase_map, supply_kpis = supply_increase_map()
    write_json("supply.json", {
        "rent_yoy": {d: fig_json(supply_rent_yoy(d), summary=rent_yoy_summary(d)) for d in districts},
        "rent_yoy_options": districts,
        "increase_map": increase_map,
        "kpis": supply_kpis,
        "district_bars": supply_district_bars(),
        "segmentation": supply_segmentation(),
    })

    pop_options = sorted(net_migration["bez_name"].replace({"Berlin Insgesamt": "All Berlin"}).unique().tolist())
    write_json("demand.json", {
        "pop_migration": {o: fig_json(demand_pop_migration(o), summary=pop_summary(o)) for o in pop_options},
        "pop_migration_options": pop_options,
        "income_line": demand_income_line(),
        "income_stack": demand_income_stack(),
    })

    by_plr = rent_burden_by_plr()
    kpis = affordability_kpis(by_plr)
    median_who, bg_who = "the median income earner", "the social welfare recipient"
    write_json("affordability.json", {
        "kpis": kpis,
        "burden_line": afford_burden_line(rent_burden_by_year()),
        "median_map": afford_map(by_plr, "rent_burden_median_income", median_who),
        "median_bins": afford_bins(by_plr["rent_burden_median_income"], True, median_who),
        "bg_map": afford_map(by_plr, "rent_burden_bg", bg_who),
        "bg_bins": afford_bins(by_plr["rent_burden_bg"], False, bg_who),
    })

    pgr = social_pgr_table()
    write_json("social.json", {
        "welfare_map": social_map(pgr, "anteil_leistungsempfaenger", "Social welfare recipients"),
        "wbs": social_wbs(),
        "subsidized_map": social_map(pgr, "anteil_sozialwohng_2022", "Subsidized housing"),
        "subsidized_bars": social_subsidized(),
        "new_units": social_new_units(),
    })

    your_rent, your_rent_data = outlook_your_rent()
    write_json("outlook.json", {"your_rent": your_rent, "your_rent_data": your_rent_data, "kpis": kpis})


if __name__ == "__main__":
    main()
