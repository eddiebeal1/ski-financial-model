"""Assumption Engine page: edit high-level assumptions for a selected scenario."""

from __future__ import annotations

import streamlit as st

from ui.bootstrap import configure_page, get_store
from ui.components.forms import assumption_set_form

configure_page("Assumptions")
store = get_store()

st.title("Assumption Engine")
st.caption("High-level business inputs only — demand, pricing, operations, inflation, capital phasing.")

scenarios = store.scenario_manager.list_scenarios()
if not scenarios:
    st.warning("No scenarios exist yet. Create one on the Scenario Builder page.")
    st.stop()

selected_name = st.selectbox("Scenario", options=[s.name for s in scenarios])
scenario = next(s for s in scenarios if s.name == selected_name)

with st.form(f"assumptions_form_{scenario.id}"):
    updated = assumption_set_form(scenario.assumption_set, key_prefix=scenario.id)
    submitted = st.form_submit_button("Save assumptions")

if submitted:
    scenario.assumption_set = updated
    st.success(f"Assumptions saved for '{scenario.name}'.")
