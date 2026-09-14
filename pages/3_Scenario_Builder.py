"""Scenario Builder page: create/clone/delete scenarios and assign projects to them."""

from __future__ import annotations

import streamlit as st

from ui.bootstrap import configure_page, get_store

configure_page("Scenario Builder")
store = get_store()
manager = store.scenario_manager
library = store.project_library

st.title("Scenario Builder")
st.caption("Baseline, Scenario A/B/C, or any number of custom scenarios.")

st.subheader("Scenarios")
scenarios = manager.list_scenarios()
for scenario in scenarios:
    badge = " (Baseline)" if scenario.is_baseline else ""
    st.write(f"**{scenario.name}{badge}** — {len(scenario.selected_projects)} project(s) selected, "
             f"${scenario.total_capital_cost():,.0f} total capital cost")

st.divider()
st.subheader("Create a New Scenario")
col1, col2 = st.columns(2)
with col1:
    new_name = st.text_input("New scenario name")
    if st.button("Create blank scenario") and new_name:
        manager.create_scenario(name=new_name)
        st.success(f"Created '{new_name}'.")
        st.rerun()
with col2:
    if scenarios:
        source_name = st.selectbox("Clone from", options=[s.name for s in scenarios], key="clone_source")
        clone_name = st.text_input("Cloned scenario name", key="clone_name")
        if st.button("Clone scenario") and clone_name:
            source = next(s for s in scenarios if s.name == source_name)
            manager.clone_scenario(source.id, clone_name)
            st.success(f"Cloned '{source_name}' as '{clone_name}'.")
            st.rerun()

st.divider()
st.subheader("Assign Capital Projects to a Scenario")
if not scenarios:
    st.info("Create a scenario first.")
    st.stop()

selected_scenario_name = st.selectbox("Scenario", options=[s.name for s in scenarios], key="assign_scenario")
scenario = next(s for s in scenarios if s.name == selected_scenario_name)

available_projects = library.list_projects()
current_ids = {p.id for p in scenario.selected_projects}
chosen_ids = st.multiselect(
    "Selected capital projects",
    options=[p.id for p in available_projects],
    default=list(current_ids),
    format_func=lambda pid: library.get_project(pid).name,
)

if st.button("Save project selection"):
    scenario.selected_projects = [library.get_project(pid) for pid in chosen_ids]
    st.success("Project selection saved.")
    st.rerun()

if scenario.is_baseline:
    st.info(f"'{scenario.name}' is the current Baseline scenario.")
elif st.button(f"Set '{scenario.name}' as Baseline"):
    manager.set_baseline(scenario.id)
    st.rerun()

if not scenario.is_baseline and st.button(f"Delete '{scenario.name}'", type="secondary"):
    manager.delete_scenario(scenario.id)
    st.rerun()
