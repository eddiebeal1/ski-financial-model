"""Capital Stack page: debt, equity, grants, and the resulting funding gap."""

from __future__ import annotations

import streamlit as st

from skimodel.capital_stack.analyzer import CapitalStackAnalyzer
from skimodel.capital_stack.models import AmortizationType, DebtTranche, EquityTranche, Grant
from ui.bootstrap import configure_page, get_store

configure_page("Capital Stack")
store = get_store()
manager = store.scenario_manager

st.title("Capital Stack Module")
st.caption("Model debt, equity, and grant funding sources for a scenario's capital program.")

scenarios = manager.list_scenarios()
if not scenarios:
    st.warning("No scenarios exist yet. Create one on the Scenario Builder page.")
    st.stop()

selected_name = st.selectbox("Scenario", options=[s.name for s in scenarios])
scenario = next(s for s in scenarios if s.name == selected_name)
structure = scenario.capital_structure

st.metric("Total Capital Project Cost", f"${scenario.total_capital_cost():,.0f}")

tab_debt, tab_equity, tab_grants = st.tabs(["Debt", "Equity", "Grants"])

with tab_debt:
    for t in structure.debt_tranches:
        st.write(f"- **{t.name}**: ${t.principal:,.0f} @ {t.interest_rate_pct}% / {t.term_years}yr ({t.amortization_type.value})")
    with st.form("add_debt_form"):
        name = st.text_input("Tranche name", value="Senior Term Loan")
        principal = st.number_input("Principal ($)", min_value=0.0, step=100_000.0)
        rate = st.number_input("Interest rate (%)", min_value=0.0, value=6.0)
        term = st.number_input("Term (years)", min_value=1, value=10)
        amort_type = st.selectbox("Amortization type", options=list(AmortizationType), format_func=lambda a: a.value.replace("_", " ").title())
        if st.form_submit_button("Add debt tranche"):
            structure.debt_tranches.append(
                DebtTranche(name=name, principal=principal, interest_rate_pct=rate, term_years=int(term), amortization_type=amort_type)
            )
            st.rerun()

with tab_equity:
    for t in structure.equity_tranches:
        st.write(f"- **{t.name}**: ${t.amount:,.0f} @ {t.required_return_pct}% required return")
    with st.form("add_equity_form"):
        name = st.text_input("Equity source name", value="Sponsor Equity")
        amount = st.number_input("Amount ($)", min_value=0.0, step=100_000.0)
        required_return = st.number_input("Required return (%)", min_value=0.0, value=15.0)
        if st.form_submit_button("Add equity tranche"):
            structure.equity_tranches.append(
                EquityTranche(name=name, amount=amount, required_return_pct=required_return)
            )
            st.rerun()

with tab_grants:
    for g in structure.grants:
        st.write(f"- **{g.name}**: ${g.amount:,.0f}")
    with st.form("add_grant_form"):
        name = st.text_input("Grant name", value="State Tourism Grant")
        amount = st.number_input("Amount ($)", min_value=0.0, step=50_000.0)
        conditions = st.text_input("Conditions", value="")
        if st.form_submit_button("Add grant"):
            structure.grants.append(Grant(name=name, amount=amount, conditions=conditions))
            st.rerun()

st.divider()
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Debt", f"${structure.total_debt():,.0f}")
col2.metric("Total Equity", f"${structure.total_equity():,.0f}")
col3.metric("Total Grants", f"${structure.total_grants():,.0f}")
gap = structure.funding_gap(scenario.total_capital_cost())
col4.metric("Funding Gap", f"${gap:,.0f}", delta=None if gap >= 0 else "Surplus")

blended_cost = CapitalStackAnalyzer.blended_cost_of_capital(structure)
st.metric("Blended Cost of Capital", f"{blended_cost:.2f}%")
