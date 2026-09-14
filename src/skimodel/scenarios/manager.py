"""Scenario lifecycle management: create, clone, delete, list, compare."""

from __future__ import annotations

from skimodel.config import DEFAULT_DISCOUNT_RATE_PCT, DEFAULT_TERMINAL_GROWTH_RATE_PCT
from skimodel.projection.engine import FinancialProjectionEngine
from skimodel.projection.results import ProjectionResults
from skimodel.scenarios.models import Scenario


class ScenarioNotFoundError(KeyError):
    pass


class ScenarioManager:
    """Owns the set of scenarios for a session, guaranteeing exactly one Baseline."""

    def __init__(self) -> None:
        self._scenarios: dict[str, Scenario] = {}

    def create_scenario(self, name: str, **kwargs: object) -> Scenario:
        """Create and register a new scenario. Supports unlimited custom scenarios."""

        scenario = Scenario(name=name, **kwargs)  # type: ignore[arg-type]
        if not self._scenarios:
            scenario.is_baseline = True
        self._scenarios[scenario.id] = scenario
        return scenario

    def clone_scenario(self, source_id: str, new_name: str) -> Scenario:
        source = self.get_scenario(source_id)
        clone = source.clone(new_name)
        self._scenarios[clone.id] = clone
        return clone

    def delete_scenario(self, scenario_id: str) -> None:
        scenario = self._scenarios.pop(scenario_id, None)
        if scenario and scenario.is_baseline and self._scenarios:
            # Promote another scenario to baseline so one always exists.
            next(iter(self._scenarios.values())).is_baseline = True

    def get_scenario(self, scenario_id: str) -> Scenario:
        try:
            return self._scenarios[scenario_id]
        except KeyError as exc:
            raise ScenarioNotFoundError(scenario_id) from exc

    def list_scenarios(self) -> list[Scenario]:
        return list(self._scenarios.values())

    def set_baseline(self, scenario_id: str) -> None:
        for scenario in self._scenarios.values():
            scenario.is_baseline = scenario.id == scenario_id

    def get_baseline(self) -> Scenario | None:
        return next((s for s in self._scenarios.values() if s.is_baseline), None)

    def run_projection(
        self,
        scenario_id: str,
        discount_rate_pct: float = DEFAULT_DISCOUNT_RATE_PCT,
        terminal_growth_rate_pct: float = DEFAULT_TERMINAL_GROWTH_RATE_PCT,
    ) -> ProjectionResults:
        scenario = self.get_scenario(scenario_id)
        engine = FinancialProjectionEngine(
            scenario=scenario,
            discount_rate_pct=discount_rate_pct,
            terminal_growth_rate_pct=terminal_growth_rate_pct,
        )
        return engine.run()

    def compare(self, scenario_ids: list[str]) -> dict[str, ProjectionResults]:
        """Run the projection engine for each requested scenario and key by name."""

        results: dict[str, ProjectionResults] = {}
        for scenario_id in scenario_ids:
            scenario = self.get_scenario(scenario_id)
            results[scenario.name] = self.run_projection(scenario_id)
        return results
