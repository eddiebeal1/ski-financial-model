"""Capital Project Library page: catalog CRUD + timing/cost assignment."""

from __future__ import annotations

import streamlit as st

from skimodel.capital_projects.models import CapitalProject, ProjectCategory
from ui.bootstrap import configure_page, get_store

configure_page("Capital Projects")
store = get_store()
library = store.project_library

st.title("Capital Project Library")
st.caption("Catalog of predefined and custom capital investments available to any scenario.")

st.subheader("Current Catalog")
df = library.to_dataframe()
if df.empty:
    st.info("The library is empty. Add a project below.")
else:
    st.dataframe(df, use_container_width=True, hide_index=True)

st.divider()
st.subheader("Add a New Project")
with st.form("add_project_form"):
    name = st.text_input("Project name")
    category = st.selectbox(
        "Category", options=list(ProjectCategory), format_func=lambda c: c.value.replace("_", " ").title()
    )
    total_cost = st.number_input("Total cost ($)", min_value=0.0, step=100_000.0)
    start_year_offset = st.number_input("Start year offset (0 = first projection year)", min_value=0, value=0)
    duration_years = st.number_input("Duration (years)", min_value=1, value=1)
    revenue_impact = st.number_input("Expected annual revenue impact ($)", value=0.0)
    opex_impact = st.number_input("Expected annual opex impact ($)", value=0.0)
    useful_life = st.number_input("Useful life (years)", min_value=1, value=15)
    description = st.text_area("Description", value="")
    submitted = st.form_submit_button("Add project")

if submitted and name:
    library.add_project(
        CapitalProject(
            name=name,
            category=category,
            total_cost=total_cost,
            start_year_offset=int(start_year_offset),
            duration_years=int(duration_years),
            expected_annual_revenue_impact=revenue_impact,
            expected_annual_opex_impact=opex_impact,
            useful_life_years=int(useful_life),
            description=description,
        )
    )
    st.success(f"Added '{name}' to the library.")
    st.rerun()

st.divider()
st.subheader("Manage Existing Projects")
projects = library.list_projects()
if projects:
    selected = st.selectbox("Select a project", options=[p.id for p in projects], format_func=lambda pid: library.get_project(pid).name)
    project = library.get_project(selected)

    col1, col2 = st.columns(2)
    with col1:
        new_start = st.number_input("Start year offset", min_value=0, value=project.start_year_offset, key="edit_start")
        new_duration = st.number_input("Duration (years)", min_value=1, value=project.duration_years, key="edit_duration")
        if st.button("Update timing"):
            library.assign_timing(project.id, int(new_start), int(new_duration))
            st.success("Timing updated.")
            st.rerun()
    with col2:
        new_cost = st.number_input("Total cost ($)", min_value=0.0, value=project.total_cost, key="edit_cost")
        if st.button("Update cost"):
            library.assign_cost(project.id, new_cost)
            st.success("Cost updated.")
            st.rerun()

    if st.button("Remove project", type="secondary"):
        library.remove_project(project.id)
        st.success("Project removed.")
        st.rerun()
