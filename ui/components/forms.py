"""Reusable Streamlit widget builders bound to skimodel dataclasses.

Keeping widget-building logic here (rather than inline in each page) means the same
form renders consistently in the Scenario Builder and Assumption Engine pages.
"""

from __future__ import annotations

import streamlit as st

from skimodel.assumptions.models import (
    AssumptionSet,
    CapitalPhasingAssumptions,
    DemandAssumptions,
    InflationAssumptions,
    OperationalAssumptions,
    PhasingStrategy,
    PricingAssumptions,
)


def demand_form(current: DemandAssumptions, key_prefix: str) -> DemandAssumptions:
    st.subheader("Demand Assumptions")
    base_visits = st.number_input(
        "Base annual skier visits", min_value=0, value=current.base_annual_skier_visits,
        step=5_000, key=f"{key_prefix}_base_visits",
    )
    growth = st.slider(
        "Annual visit growth rate (%)", -5.0, 15.0, current.annual_visit_growth_rate_pct,
        key=f"{key_prefix}_visit_growth",
    )
    capture = st.slider(
        "Market capture rate (%)", 0.0, 100.0, current.market_capture_rate_pct,
        key=f"{key_prefix}_capture",
    )
    return DemandAssumptions(
        base_annual_skier_visits=int(base_visits),
        annual_visit_growth_rate_pct=growth,
        market_capture_rate_pct=capture,
    )


def pricing_form(current: PricingAssumptions, key_prefix: str) -> PricingAssumptions:
    st.subheader("Pricing Assumptions")
    ticket = st.number_input(
        "Base walk-up ticket price ($)", min_value=0.0, value=current.base_walk_up_ticket_price,
        key=f"{key_prefix}_ticket",
    )
    growth = st.slider(
        "Annual price growth rate (%)", -5.0, 15.0, current.annual_price_growth_rate_pct,
        key=f"{key_prefix}_price_growth",
    )
    ancillary = st.number_input(
        "Ancillary spend per visit ($)", min_value=0.0, value=current.ancillary_spend_per_visit,
        key=f"{key_prefix}_ancillary",
    )
    pass_mix = st.slider(
        "Season pass mix (%)", 0.0, 100.0, current.season_pass_mix_pct,
        key=f"{key_prefix}_pass_mix",
    )
    pass_price = st.number_input(
        "Season pass effective price ($)", min_value=0.0, value=current.season_pass_effective_price,
        key=f"{key_prefix}_pass_price",
    )
    return PricingAssumptions(
        base_walk_up_ticket_price=ticket,
        annual_price_growth_rate_pct=growth,
        ancillary_spend_per_visit=ancillary,
        season_pass_mix_pct=pass_mix,
        season_pass_effective_price=pass_price,
    )


def operational_form(current: OperationalAssumptions, key_prefix: str) -> OperationalAssumptions:
    st.subheader("Operational Assumptions")
    fixed = st.number_input(
        "Fixed opex, annual ($)", min_value=0.0, value=current.fixed_opex_annual,
        key=f"{key_prefix}_fixed_opex",
    )
    variable_pct = st.slider(
        "Variable opex (% of revenue)", 0.0, 100.0, current.variable_opex_pct_of_revenue,
        key=f"{key_prefix}_variable_opex",
    )
    opex_growth = st.slider(
        "Opex growth rate (%)", -5.0, 15.0, current.opex_growth_rate_pct,
        key=f"{key_prefix}_opex_growth",
    )
    labor_inflation = st.slider(
        "Labor cost inflation (%)", 0.0, 15.0, current.labor_cost_inflation_pct,
        key=f"{key_prefix}_labor_inflation",
    )
    maint_capex_pct = st.slider(
        "Maintenance capex (% of revenue)", 0.0, 20.0, current.maintenance_capex_pct_of_revenue,
        key=f"{key_prefix}_maint_capex",
    )
    return OperationalAssumptions(
        fixed_opex_annual=fixed,
        variable_opex_pct_of_revenue=variable_pct,
        opex_growth_rate_pct=opex_growth,
        labor_cost_inflation_pct=labor_inflation,
        maintenance_capex_pct_of_revenue=maint_capex_pct,
    )


def inflation_form(current: InflationAssumptions, key_prefix: str) -> InflationAssumptions:
    st.subheader("Inflation Assumptions")
    general = st.slider("General inflation (%)", 0.0, 15.0, current.general_inflation_pct, key=f"{key_prefix}_general")
    labor = st.slider("Labor inflation (%)", 0.0, 15.0, current.labor_inflation_pct, key=f"{key_prefix}_labor")
    energy = st.slider("Energy inflation (%)", 0.0, 15.0, current.energy_inflation_pct, key=f"{key_prefix}_energy")
    return InflationAssumptions(
        general_inflation_pct=general, labor_inflation_pct=labor, energy_inflation_pct=energy
    )


def capital_phasing_form(
    current: CapitalPhasingAssumptions, key_prefix: str
) -> CapitalPhasingAssumptions:
    st.subheader("Capital Phasing Assumptions")
    horizon = st.slider(
        "Planning horizon (years)", 3, 20, current.planning_horizon_years,
        key=f"{key_prefix}_horizon",
    )
    strategy = st.selectbox(
        "Phasing strategy",
        options=list(PhasingStrategy),
        format_func=lambda s: s.value.replace("_", " ").title(),
        index=list(PhasingStrategy).index(current.phasing_strategy),
        key=f"{key_prefix}_strategy",
    )
    return CapitalPhasingAssumptions(
        planning_horizon_years=horizon,
        phasing_strategy=strategy,
        custom_phasing_weights=current.custom_phasing_weights,
    )


def assumption_set_form(current: AssumptionSet, key_prefix: str) -> AssumptionSet:
    """Render the full Assumption Engine form and return the updated AssumptionSet."""

    start_year = st.number_input(
        "Projection start year", min_value=2000, max_value=2100, value=current.start_year,
        key=f"{key_prefix}_start_year",
    )
    demand = demand_form(current.demand, key_prefix)
    pricing = pricing_form(current.pricing, key_prefix)
    operations = operational_form(current.operations, key_prefix)
    inflation = inflation_form(current.inflation, key_prefix)
    capital_phasing = capital_phasing_form(current.capital_phasing, key_prefix)

    return AssumptionSet(
        start_year=int(start_year),
        demand=demand,
        pricing=pricing,
        operations=operations,
        inflation=inflation,
        capital_phasing=capital_phasing,
    )
