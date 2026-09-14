"""Immutable output of a financial projection run."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass(frozen=True)
class ProjectionResults:
    """Year-by-year projection output plus summary valuation metrics.

    All list fields are aligned by index to ``years`` (calendar years).
    """

    scenario_name: str
    years: list[int]
    revenue: list[float]
    opex: list[float]
    ebitda: list[float]
    maintenance_capex: list[float]
    project_capex: list[float]
    debt_service: list[float]
    taxes: list[float]
    free_cash_flow: list[float]
    npv: float
    irr: float | None
    enterprise_value: float
    terminal_value: float
    total_capital_cost: float
    funding_gap: float

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "year": self.years,
                "revenue": self.revenue,
                "opex": self.opex,
                "ebitda": self.ebitda,
                "maintenance_capex": self.maintenance_capex,
                "project_capex": self.project_capex,
                "debt_service": self.debt_service,
                "taxes": self.taxes,
                "free_cash_flow": self.free_cash_flow,
            }
        )

    def ebitda_margin_pct(self) -> list[float]:
        return [
            (e / r * 100.0) if r else 0.0 for e, r in zip(self.ebitda, self.revenue)
        ]

    def revenue_cagr_pct(self) -> float:
        if len(self.revenue) < 2 or self.revenue[0] <= 0:
            return 0.0
        n = len(self.revenue) - 1
        return ((self.revenue[-1] / self.revenue[0]) ** (1 / n) - 1) * 100.0
