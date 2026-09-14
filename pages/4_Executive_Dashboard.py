"""Executive Dashboard page: KPI cards, charts, and scenario comparisons."""

from __future__ import annotations

import streamlit as st

from skimodel.dashboard.charts import (
    capex_phasing_chart,
    fcf_waterfall,
    revenue_ebitda_chart,
    scenario_comparison_chart,
)
from skimodel.dashboard.comparisons import compare_scenarios
from skimodel.dashboard.kpi import build_kpi_cards
from ui.bootstrap import configure_page, get_store

configure_page("Executive Dashboard")
store = get_store()
manager = store.scenario_manager

st.title("Executive Dashboard")

scenarios = manager.list_scenarios()
if not scenarios:
    st.warning("No scenarios exist yet. Create one on the Scenario Builder page.")
    st.stop()

selected_name = st.selectbox("Focus scenario", options=[s.name for s in scenarios])
scenario = next(s for s in scenarios if s.name == selected_name)
results = manager.run_projection(scenario.id)

st.subheader(f"Key Metrics — {scenario.name}")
cards = build_kpi_cards(results)
cols = st.columns(len(cards))
for col, card in zip(cols, cards):
    col.metric(card["label"], card["value"], help=card["help_text"])

st.divider()
col_a, col_b = st.columns(2)
col_a.plotly_chart(revenue_ebitda_chart(results), use_container_width=True)
col_b.plotly_chart(capex_phasing_chart(results), use_container_width=True)
st.plotly_chart(fcf_waterfall(results), use_container_width=True)

st.divider()
st.subheader("Scenario Comparison")
compare_names = st.multiselect(
    "Scenarios to compare", options=[s.name for s in scenarios], default=[s.name for s in scenarios]
)
if compare_names:
    ids = [s.id for s in scenarios if s.name in compare_names]
    results_by_name = manager.compare(ids)

    metric = st.selectbox(
        "Comparison metric", options=["revenue", "ebitda", "free_cash_flow"], format_func=lambda m: m.replace("_", " ").title()
    )
    st.plotly_chart(scenario_comparison_chart(results_by_name, metric), use_container_width=True)
    st.dataframe(compare_scenarios(results_by_name), use_container_width=True)
