"""Plotly figure builders for the Executive Dashboard."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from skimodel.projection.results import ProjectionResults


def revenue_ebitda_chart(results: ProjectionResults) -> go.Figure:
    df = results.to_dataframe()
    fig = go.Figure()
    fig.add_bar(x=df["year"], y=df["revenue"], name="Revenue")
    fig.add_scatter(x=df["year"], y=df["ebitda"], name="EBITDA", mode="lines+markers")
    fig.update_layout(
        title="Revenue & EBITDA",
        xaxis_title="Year",
        yaxis_title="$",
        barmode="group",
    )
    return fig


def fcf_waterfall(results: ProjectionResults) -> go.Figure:
    df = results.to_dataframe()
    fig = go.Figure(
        go.Waterfall(
            x=[
                "EBITDA",
                "Maintenance Capex",
                "Project Capex",
                "Debt Service",
                "Taxes",
                "Free Cash Flow",
            ],
            measure=["relative", "relative", "relative", "relative", "relative", "total"],
            y=[
                df["ebitda"].sum(),
                -df["maintenance_capex"].sum(),
                -df["project_capex"].sum(),
                -df["debt_service"].sum(),
                -df["taxes"].sum(),
                df["free_cash_flow"].sum(),
            ],
        )
    )
    fig.update_layout(title="Cumulative Free Cash Flow Bridge (Full Horizon)")
    return fig


def capex_phasing_chart(results: ProjectionResults) -> go.Figure:
    df = results.to_dataframe()
    fig = px.bar(df, x="year", y="project_capex", title="Capital Project Spend by Year")
    fig.update_layout(xaxis_title="Year", yaxis_title="$")
    return fig


def scenario_comparison_chart(
    results_by_name: dict[str, ProjectionResults], metric: str = "ebitda"
) -> go.Figure:
    """Line chart comparing a single metric (e.g. 'revenue', 'ebitda', 'free_cash_flow')
    across multiple scenarios."""

    frames = []
    for name, results in results_by_name.items():
        df = results.to_dataframe()[["year", metric]].copy()
        df["scenario"] = name
        frames.append(df)
    combined = pd.concat(frames, ignore_index=True)
    fig = px.line(
        combined, x="year", y=metric, color="scenario", markers=True,
        title=f"Scenario Comparison — {metric.replace('_', ' ').title()}",
    )
    return fig
