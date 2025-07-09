import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.graph_objects as go
from data_loader import load_pop_BEZ, load_net_migration, load_income_persons, load_income_households

pop_BEZ = load_pop_BEZ()
net_migration = load_net_migration()
income_persons = load_income_persons()
income_households = load_income_households()

def show_demand_tab():
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
        income_persons["monthly_disposable_income"] = (
            income_persons["monthly_disposable_income"]
            .astype(str)
            .str.replace(",", ".", regex=False)
            .astype(float))

        # Create chart
        fig_income_line = go.Figure()

        fig_income_line.add_trace(go.Scatter(
            x=income_persons["year"],
            y=income_persons["monthly_disposable_income"],
            mode="lines+markers",
            name="Monthly Net Income",
            line=dict(color="black", width=2),
            marker=dict(size=6, color="black"),
            hovertemplate="Year: %{x}<br>Income: %{y:.2f} €<extra></extra>"
        ))

        # Annotate last value
        last_year = income_persons["year"].iloc[-1]
        last_value = income_persons["monthly_disposable_income"].iloc[-1]

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
            income_households[col] = (
                income_households[col]
                .astype(str)
                .str.replace(",", ".", regex=False)
                .astype(float))

        orange_gradient_income = [
            "#FEE2D5", "#FDB99B", "#FC8C5C", "#F86A3C", "#D4583B"]

        fig_income_stack = go.Figure()

        for col, color in zip(income_cols, orange_gradient_income):
            label = col.replace("%_", "").replace("_", "–").replace("over", "Over ")
            fig_income_stack.add_trace(go.Scatter(
                x=income_households["year"],
                y=income_households[col],
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
            year_data = income_households[income_households["year"] == year]
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