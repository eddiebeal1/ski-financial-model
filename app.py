"""Streamlit entrypoint for the Ski Resort Capital Planning consulting deliverable.

Run with: streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

from ui.bootstrap import configure_page, get_store

configure_page("Home")
store = get_store()

st.title("🎿 Ski Resort Capital Planning & Financial Strategy")
st.caption(
    "An interactive consulting deliverable for evaluating strategic alternatives and "
    "capital investment scenarios — not a replacement for detailed Excel modeling."
)

st.markdown(
    """
    Use the pages in the left sidebar to work through the analysis:

    1. **Assumptions** — set demand, pricing, operational, inflation, and capital
       phasing assumptions for each scenario.
    2. **Capital Projects** — manage the shared catalog of capital investments and
       assign timing/cost.
    3. **Scenario Builder** — create Baseline, Scenario A/B/C, or any number of custom
       scenarios by combining assumptions and selected projects.
    4. **Executive Dashboard** — review KPI cards, charts, and side-by-side scenario
       comparisons.
    5. **Capital Stack** — model debt, equity, and grant funding sources and see the
       resulting funding gap.
    """
)

col1, col2, col3 = st.columns(3)
col1.metric("Scenarios", len(store.scenario_manager.list_scenarios()))
col2.metric("Capital Projects in Library", len(store.project_library.list_projects()))
baseline = store.scenario_manager.get_baseline()
col3.metric("Baseline Scenario", baseline.name if baseline else "None")
