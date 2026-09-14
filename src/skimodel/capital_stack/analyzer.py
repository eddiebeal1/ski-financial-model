"""Debt amortization, funding gap, and blended cost of capital calculations."""

from __future__ import annotations

import pandas as pd

from skimodel.capital_stack.models import AmortizationType, CapitalStructure, DebtTranche


class CapitalStackAnalyzer:
    """Stateless helper functions operating on a ``CapitalStructure``."""

    @staticmethod
    def build_debt_schedule(tranche: DebtTranche) -> pd.DataFrame:
        """Return a year-indexed amortization schedule for a single debt tranche.

        Columns: year_offset, beginning_balance, interest, principal_payment,
        ending_balance, total_debt_service.
        """

        rate = tranche.interest_rate_pct / 100.0
        years = list(range(tranche.draw_year_offset, tranche.draw_year_offset + tranche.term_years))
        rows = []
        balance = tranche.principal

        if tranche.amortization_type == AmortizationType.AMORTIZING and rate > 0:
            # Level annual payment (mortgage-style) covering interest + principal.
            annuity_factor = rate / (1 - (1 + rate) ** -tranche.term_years)
            level_payment = tranche.principal * annuity_factor
        else:
            level_payment = None

        for year in years:
            interest = balance * rate
            if tranche.amortization_type == AmortizationType.INTEREST_ONLY:
                principal_payment = 0.0
            elif tranche.amortization_type == AmortizationType.BULLET:
                principal_payment = tranche.principal if year == years[-1] else 0.0
            else:  # AMORTIZING
                principal_payment = (
                    (level_payment - interest) if level_payment is not None
                    else tranche.principal / tranche.term_years
                )
            principal_payment = min(principal_payment, balance)
            ending_balance = balance - principal_payment
            rows.append(
                {
                    "year_offset": year,
                    "beginning_balance": balance,
                    "interest": interest,
                    "principal_payment": principal_payment,
                    "ending_balance": ending_balance,
                    "total_debt_service": interest + principal_payment,
                }
            )
            balance = ending_balance

        return pd.DataFrame(rows)

    @classmethod
    def build_consolidated_debt_service(
        cls, structure: CapitalStructure, horizon_years: int
    ) -> pd.Series:
        """Sum debt service across all tranches for each year offset in the horizon."""

        service = pd.Series(0.0, index=range(horizon_years))
        for tranche in structure.debt_tranches:
            schedule = cls.build_debt_schedule(tranche)
            for _, row in schedule.iterrows():
                offset = int(row["year_offset"])
                if offset in service.index:
                    service.loc[offset] += row["total_debt_service"]
        return service

    @staticmethod
    def compute_funding_gap(structure: CapitalStructure, total_project_cost: float) -> float:
        return structure.funding_gap(total_project_cost)

    @staticmethod
    def blended_cost_of_capital(structure: CapitalStructure) -> float:
        """Weighted-average cost of capital across debt and equity (grants are free money)."""

        total_debt = structure.total_debt()
        total_equity = structure.total_equity()
        weighted_capital = total_debt + total_equity
        if weighted_capital == 0:
            return 0.0

        debt_cost = sum(t.principal * (t.interest_rate_pct / 100.0) for t in structure.debt_tranches)
        equity_cost = sum(
            t.amount * (t.required_return_pct / 100.0) for t in structure.equity_tranches
        )
        return (debt_cost + equity_cost) / weighted_capital * 100.0
