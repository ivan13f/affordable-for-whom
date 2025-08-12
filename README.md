# Affordable for Whom? — Berlin Rental Affordability (2013–2023)

**Live app** → affordable-for-whom.streamlit.app

A data storytelling project exploring how affordable renting in Berlin really is — and for whom. The app brings together rent listings, income, population, and social/subsidized housing data to show how affordability evolved from 2013 to 2023, and lets you test affordability for different incomes and flat sizes.

This project was built as a Data Analytics bootcamp capstone and combines data analysis, mapping, and UX to communicate a complex topic accessibly.

## Motivation
Berlin’s reputation for “cheap living” has eroded. Rents rose fast; incomes rose too, but unevenly; and the stock of subsidized housing shrank. Behind citywide averages are stark spatial differences. This project asks: Who can still afford to rent, where, and how has that changed over time?

## What the App Shows
- Rent market evolution (2013–2023): changes in €/m² and areas where prices doubled
- Demand signals: population growth, net migration, income trends
- Affordability: rent burden maps (share of income spent on rent)
- Access to social/subsidized housing: WBS & public housing trends
- Your rent: interactive map to test affordability by income and apartment size

## How Affordability Is Calculated
**Rent burden** = (median rent €/m² × apartment size m²) ÷ monthly income

**Baseline sizes:** 1-room 50 m², 2-room 65 m², 3-room 80 m²

**Affordability threshold:** 30% of income (clearly marked in the color scale)

**PLR** = Planungsräume (LOR planning areas), the unit used for spatial analysis

## Data Sources & Attributions

This project aggregates publicly available statistics and official geodata for Berlin.

| Source | Description |
|---|---|
| Amt für Statistik Berlin-Brandenburg **(AfS)** | Population by PLR, Income 2022–2024, Household data 2023 |
| [Investitions Bank Berlin Housing Market Reports **(IBB)**](https://www.ibb.de/de/ueber-uns/publikationen/wohnungsmarktbericht/2024.html#iframe_angebotsmieten) | Median and Average Rent prices by PLR 2013–2014, Rent Trends |
| Bundesagentur für Arbeit **(AfA)** | 	Unemployment rates, Bürgergeld caps |
| [Wohnatlas 2022](https://www.berlin.de/sen/wohnen/service/berliner-wohnungsmarkt/wohnatlas-berlin) Senatsverwaltung für Stadtentwicklung, Bauen und Wohnen **(SenStadt)** | Social housing %, Social Welfare Recipients %, Geographic Information |
| Verband Berlin-Brandenburgischer Wohnungsunternehmen **(BBU)** | 	Social Housing data for 2017–2023 |

## Context
Created as the capstone project for a Data Analytics bootcamp. The goal is to demonstrate end-to-end skills: data collection/cleaning, spatial analysis, interactive visualization, and narrative design.
