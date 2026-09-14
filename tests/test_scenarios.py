from skimodel.scenarios.manager import ScenarioManager, ScenarioNotFoundError
import pytest


def test_first_created_scenario_is_baseline():
    manager = ScenarioManager()
    scenario = manager.create_scenario(name="Baseline")
    assert scenario.is_baseline is True


def test_second_scenario_is_not_baseline():
    manager = ScenarioManager()
    manager.create_scenario(name="Baseline")
    scenario_a = manager.create_scenario(name="Scenario A")
    assert scenario_a.is_baseline is False


def test_clone_scenario_deep_copies_assumptions():
    manager = ScenarioManager()
    baseline = manager.create_scenario(name="Baseline")
    baseline.assumption_set.demand.base_annual_skier_visits = 500_000
    clone = manager.clone_scenario(baseline.id, "Scenario A")
    clone.assumption_set.demand.base_annual_skier_visits = 999
    assert baseline.assumption_set.demand.base_annual_skier_visits == 500_000
    assert clone.is_baseline is False
    assert clone.name == "Scenario A"


def test_delete_baseline_promotes_another_scenario():
    manager = ScenarioManager()
    baseline = manager.create_scenario(name="Baseline")
    other = manager.create_scenario(name="Scenario A")
    manager.delete_scenario(baseline.id)
    assert other.is_baseline is True


def test_get_missing_scenario_raises():
    manager = ScenarioManager()
    with pytest.raises(ScenarioNotFoundError):
        manager.get_scenario("does-not-exist")


def test_unlimited_custom_scenarios():
    manager = ScenarioManager()
    for i in range(10):
        manager.create_scenario(name=f"Custom {i}")
    assert len(manager.list_scenarios()) == 10
