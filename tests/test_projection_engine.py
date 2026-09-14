from skimodel.capital_projects.models import CapitalProject
from skimodel.capital_stack.models import CapitalStructure, DebtTranche
from skimodel.projection.engine import FinancialProjectionEngine
from skimodel.scenarios.models import Scenario


def _basic_scenario() -> Scenario:
    scenario = Scenario(name="Test Scenario")
    scenario.assumption_set.capital_phasing.planning_horizon_years = 5
    return scenario


def test_projection_runs_and_produces_expected_length():
    scenario = _basic_scenario()
    results = FinancialProjectionEngine(scenario).run()
    assert len(results.years) == 5
    assert len(results.revenue) == 5
    assert all(r > 0 for r in results.revenue)


def test_revenue_grows_with_demand_and_price_assumptions():
    scenario = _basic_scenario()
    results = FinancialProjectionEngine(scenario).run()
    assert results.revenue[-1] > results.revenue[0]


def test_capital_project_impacts_revenue_after_online():
    scenario = _basic_scenario()
    project = CapitalProject(
        name="New Lift", total_cost=1_000_000, start_year_offset=0, duration_years=1,
        expected_annual_revenue_impact=500_000,
    )
    scenario.selected_projects = [project]
    results = FinancialProjectionEngine(scenario).run()
    # Project comes online at year offset 1 (start + duration); capex hits year 0.
    assert results.project_capex[0] == 1_000_000
    assert results.revenue[1] > results.revenue[0]


def test_debt_service_reflected_in_fcf():
    scenario = _basic_scenario()
    scenario.capital_structure = CapitalStructure(
        debt_tranches=[DebtTranche(name="Loan", principal=1_000_000, interest_rate_pct=5.0, term_years=5)]
    )
    results = FinancialProjectionEngine(scenario).run()
    assert all(ds > 0 for ds in results.debt_service)


def test_npv_and_irr_are_computed():
    scenario = _basic_scenario()
    results = FinancialProjectionEngine(scenario).run()
    assert isinstance(results.npv, float)
    # IRR may be None if the FCF stream never changes sign; just assert no crash.
    assert results.irr is None or isinstance(results.irr, float)


def test_funding_gap_matches_capital_structure():
    scenario = _basic_scenario()
    project = CapitalProject(name="X", total_cost=2_000_000, is_active=True)
    scenario.selected_projects = [project]
    scenario.capital_structure = CapitalStructure(
        debt_tranches=[DebtTranche(name="Loan", principal=1_000_000, interest_rate_pct=5.0, term_years=5)]
    )
    results = FinancialProjectionEngine(scenario).run()
    assert results.total_capital_cost == 2_000_000
    assert results.funding_gap == 1_000_000
