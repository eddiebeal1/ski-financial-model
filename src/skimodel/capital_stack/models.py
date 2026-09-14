"""Capital stack (funding sources) data model."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum


class AmortizationType(str, Enum):
    INTEREST_ONLY = "interest_only"
    AMORTIZING = "amortizing"
    BULLET = "bullet"


@dataclass
class DebtTranche:
    name: str
    principal: float
    interest_rate_pct: float
    term_years: int
    amortization_type: AmortizationType = AmortizationType.AMORTIZING
    draw_year_offset: int = 0
    """Year offset at which the tranche is drawn/originated."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class EquityTranche:
    name: str
    amount: float
    required_return_pct: float
    contribution_year_offset: int = 0
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class Grant:
    name: str
    amount: float
    year_received_offset: int = 0
    conditions: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class CapitalStructure:
    """Full funding stack backing a scenario's capital program."""

    debt_tranches: list[DebtTranche] = field(default_factory=list)
    equity_tranches: list[EquityTranche] = field(default_factory=list)
    grants: list[Grant] = field(default_factory=list)

    def total_debt(self) -> float:
        return sum(t.principal for t in self.debt_tranches)

    def total_equity(self) -> float:
        return sum(t.amount for t in self.equity_tranches)

    def total_grants(self) -> float:
        return sum(g.amount for g in self.grants)

    def total_funding(self) -> float:
        return self.total_debt() + self.total_equity() + self.total_grants()

    def funding_gap(self, total_project_cost: float) -> float:
        """Positive value = shortfall still needing to be raised; negative = surplus."""

        return total_project_cost - self.total_funding()
