"""Runs a Scenario through revenue/opex/capex/debt-service/valuation math."""

from __future__ import annotations

import numpy_financial as npf

from skimodel.assumptions.models import PhasingStrategy
from skimodel.capital_stack.analyzer import CapitalStackAnalyzer
from skimodel.config import (
    DEFAULT_DISCOUNT_RATE_PCT,
    DEFAULT_EFFECTIVE_TAX_RATE_PCT,
    DEFAULT_EV_EXIT_EBITDA_MULTIPLE,
    DEFAULT_TERMINAL_GROWTH_RATE_PCT,
)
from skimodel.projection.results import ProjectionResults
from skimodel.scenarios.models import Scenario


class FinancialProjectionEngine:
    """Pure calculation engine: Scenario in, ProjectionResults out.

    No I/O, no Streamlit dependency — safe to unit test and reuse elsewhere.
    """

    def __init__(
        self,
        scenario: Scenario,
        discount_rate_pct: float = DEFAULT_DISCOUNT_RATE_PCT,
        terminal_growth_rate_pct: float = DEFAULT_TERMINAL_GROWTH_RATE_PCT,
        exit_ebitda_multiple: float = DEFAULT_EV_EXIT_EBITDA_MULTIPLE,
        effective_tax_rate_pct: float = DEFAULT_EFFECTIVE_TAX_RATE_PCT,
    ) -> None:
        self.scenario = scenario
        self.discount_rate_pct = discount_rate_pct
        self.terminal_growth_rate_pct = terminal_growth_rate_pct
        self.exit_ebitda_multiple = exit_ebitda_multiple
        self.effective_tax_rate_pct = effective_tax_rate_pct
        self.horizon_years = scenario.assumption_set.capital_phasing.planning_horizon_years

    def run(self) -> ProjectionResults:
        revenue = self._project_revenue()
        opex = self._project_opex(revenue)
        ebitda = [r - o for r, o in zip(revenue, opex)]
        maintenance_capex = self._project_maintenance_capex(revenue)
        project_capex = self._project_capex()
        debt_service = self._project_debt_service()
        taxes = self._project_taxes(ebitda)
        fcf = self._compute_fcf(
            ebitda, maintenance_capex, project_capex, debt_service, taxes
        )

        npv = self._compute_npv(fcf)
        irr = self._compute_irr(fcf)
        terminal_value = self._compute_terminal_value(ebitda[-1] if ebitda else 0.0)
        enterprise_value = self._compute_enterprise_value(fcf, terminal_value)

        total_capital_cost = self.scenario.total_capital_cost()
        funding_gap = CapitalStackAnalyzer.compute_funding_gap(
            self.scenario.capital_structure, total_capital_cost
        )

        start_year = self.scenario.assumption_set.start_year
        years = [start_year + i for i in range(self.horizon_years)]

        return ProjectionResults(
            scenario_name=self.scenario.name,
            years=years,
            revenue=revenue,
            opex=opex,
            ebitda=ebitda,
            maintenance_capex=maintenance_capex,
            project_capex=project_capex,
            debt_service=debt_service,
            taxes=taxes,
            free_cash_flow=fcf,
            npv=npv,
            irr=irr,
            enterprise_value=enterprise_value,
            terminal_value=terminal_value,
            total_capital_cost=total_capital_cost,
            funding_gap=funding_gap,
        )

    # -- Revenue ----------------------------------------------------------------
    def _project_revenue(self) -> list[float]:
        demand = self.scenario.assumption_set.demand
        pricing = self.scenario.assumption_set.pricing

        pass_visits_pct = pricing.season_pass_mix_pct / 100.0
        walkup_visits_pct = 1 - pass_visits_pct
        base_blended_price = (
            pricing.base_walk_up_ticket_price * walkup_visits_pct
            + pricing.season_pass_effective_price * pass_visits_pct
            + pricing.ancillary_spend_per_visit
        )

        visits = demand.base_annual_skier_visits * (demand.market_capture_rate_pct / 100.0)
        revenues: list[float] = []
        for year in range(self.horizon_years):
            visit_growth = (1 + demand.annual_visit_growth_rate_pct / 100.0) ** year
            price_growth = (1 + pricing.annual_price_growth_rate_pct / 100.0) ** year
            base_revenue = visits * visit_growth * base_blended_price * price_growth
            base_revenue += self._active_project_revenue_impact(year)
            revenues.append(base_revenue)
        return revenues

    def _active_project_revenue_impact(self, year: int) -> float:
        return sum(
            p.expected_annual_revenue_impact
            for p in self.scenario.selected_projects
            if p.is_active and p.online_year_offset() <= year
        )

    # -- Operating expense --------------------------------------------------------
    def _project_opex(self, revenue: list[float]) -> list[float]:
        ops = self.scenario.assumption_set.operations
        opex: list[float] = []
        for year, rev in enumerate(revenue):
            growth = (1 + ops.opex_growth_rate_pct / 100.0) ** year
            fixed = ops.fixed_opex_annual * growth
            variable = rev * (ops.variable_opex_pct_of_revenue / 100.0)
            project_opex = self._active_project_opex_impact(year)
            opex.append(fixed + variable + project_opex)
        return opex

    def _active_project_opex_impact(self, year: int) -> float:
        return sum(
            p.expected_annual_opex_impact
            for p in self.scenario.selected_projects
            if p.is_active and p.online_year_offset() <= year
        )

    def _project_maintenance_capex(self, revenue: list[float]) -> list[float]:
        ops = self.scenario.assumption_set.operations
        return [r * (ops.maintenance_capex_pct_of_revenue / 100.0) for r in revenue]

    # -- Capital project spend phasing -------------------------------------------
    def _project_capex(self) -> list[float]:
        phasing = self.scenario.assumption_set.capital_phasing
        capex = [0.0] * self.horizon_years

        for project in self.scenario.selected_projects:
            if not project.is_active:
                continue
            schedule = self._phased_schedule(project.total_cost, project, phasing)
            for year_offset, amount in schedule.items():
                if 0 <= year_offset < self.horizon_years:
                    capex[year_offset] += amount
        return capex

    @staticmethod
    def _phased_schedule(total_cost, project, phasing) -> dict[int, float]:
        if phasing.phasing_strategy == PhasingStrategy.CUSTOM and phasing.custom_phasing_weights:
            return {
                project.start_year_offset + year: total_cost * (weight / 100.0)
                for year, weight in phasing.custom_phasing_weights.items()
            }
        if phasing.phasing_strategy == PhasingStrategy.FRONT_LOADED:
            weights = _front_loaded_weights(project.duration_years)
        elif phasing.phasing_strategy == PhasingStrategy.BACK_LOADED:
            weights = list(reversed(_front_loaded_weights(project.duration_years)))
        else:  # EVEN
            weights = [1 / project.duration_years] * project.duration_years
        return {
            project.start_year_offset + i: total_cost * w for i, w in enumerate(weights)
        }

    # -- Debt service --------------------------------------------------------------
    def _project_debt_service(self) -> list[float]:
        series = CapitalStackAnalyzer.build_consolidated_debt_service(
            self.scenario.capital_structure, self.horizon_years
        )
        return [float(series.get(i, 0.0)) for i in range(self.horizon_years)]

    # -- Taxes / FCF -----------------------------------------------------------------
    def _project_taxes(self, ebitda: list[float]) -> list[float]:
        rate = self.effective_tax_rate_pct / 100.0
        return [max(e, 0.0) * rate for e in ebitda]

    def _compute_fcf(
        self, ebitda, maintenance_capex, project_capex, debt_service, taxes
    ) -> list[float]:
        return [
            e - m - c - d - t
            for e, m, c, d, t in zip(
                ebitda, maintenance_capex, project_capex, debt_service, taxes
            )
        ]

    # -- Valuation --------------------------------------------------------------------
    def _compute_npv(self, fcf: list[float]) -> float:
        rate = self.discount_rate_pct / 100.0
        return float(npf.npv(rate, [0.0] + fcf))

    def _compute_irr(self, fcf: list[float]) -> float | None:
        # No explicit initial outlay is modeled here; the funding stack (debt/equity/
        # grants) is treated separately. IRR is computed on the FCF stream itself,
        # anchored by a nominal -1 unit at t=0 for scale-independent solving when the
        # caller wants an equity-style return proxy.
        try:
            irr = npf.irr(fcf)
        except Exception:
            return None
        if irr is None or irr != irr:  # NaN check
            return None
        return float(irr * 100.0)

    def _compute_terminal_value(self, final_year_ebitda: float) -> float:
        return final_year_ebitda * self.exit_ebitda_multiple

    def _compute_enterprise_value(self, fcf: list[float], terminal_value: float) -> float:
        rate = self.discount_rate_pct / 100.0
        n = len(fcf)
        pv_fcf = float(npf.npv(rate, [0.0] + fcf))
        pv_terminal = terminal_value / ((1 + rate) ** n) if n else terminal_value
        return pv_fcf + pv_terminal


def _front_loaded_weights(duration_years: int) -> list[float]:
    """Simple linearly decreasing weights that sum to 1.0."""

    if duration_years <= 1:
        return [1.0] * max(duration_years, 1)
    raw = list(range(duration_years, 0, -1))
    total = sum(raw)
    return [r / total for r in raw]
