from skimodel.assumptions.defaults import default_assumption_set
from skimodel.assumptions.models import AssumptionSet, PhasingStrategy


def test_default_assumption_set_returns_fresh_instances():
    a = default_assumption_set()
    b = default_assumption_set()
    assert a is not b
    assert a.demand is not b.demand
    a.demand.base_annual_skier_visits = 999
    assert b.demand.base_annual_skier_visits != 999


def test_assumption_set_defaults():
    a = AssumptionSet()
    assert a.capital_phasing.phasing_strategy == PhasingStrategy.EVEN
    assert a.capital_phasing.planning_horizon_years == 10
