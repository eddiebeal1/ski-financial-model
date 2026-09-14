"""High-level business assumption dataclasses.

Each dataclass represents one assumption category surfaced in the Assumption Engine
page of the UI. Fields are intentionally coarse-grained (business-level) rather than
line-item accounting detail.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class PhasingStrategy(str, Enum):
    FRONT_LOADED = "front_loaded"
    EVEN = "even"
    BACK_LOADED = "back_loaded"
    CUSTOM = "custom"


@dataclass
class DemandAssumptions:
    """Skier-visit demand drivers."""

    base_annual_skier_visits: int = 250_000
    annual_visit_growth_rate_pct: float = 1.5
    market_capture_rate_pct: float = 100.0
    """Share of addressable regional demand this resort expects to capture."""


@dataclass
class PricingAssumptions:
    """Ticket and ancillary pricing drivers."""

    base_walk_up_ticket_price: float = 129.0
    annual_price_growth_rate_pct: float = 3.0
    ancillary_spend_per_visit: float = 45.0
    """Food & beverage, rental, retail, lessons spend per visit."""
    season_pass_mix_pct: float = 40.0
    """Share of visits attributable to season pass holders (typically lower yield)."""
    season_pass_effective_price: float = 65.0
    """Blended effective per-visit price realized from season pass holders."""


@dataclass
class OperationalAssumptions:
    """Cost structure and operating leverage drivers."""

    fixed_opex_annual: float = 12_000_000.0
    variable_opex_pct_of_revenue: float = 35.0
    opex_growth_rate_pct: float = 3.0
    labor_cost_inflation_pct: float = 4.0
    maintenance_capex_pct_of_revenue: float = 4.0
    """Recurring maintenance capex, distinct from discretionary capital projects."""


@dataclass
class InflationAssumptions:
    """Macro inflation drivers applied across cost lines."""

    general_inflation_pct: float = 2.5
    labor_inflation_pct: float = 4.0
    energy_inflation_pct: float = 5.0


@dataclass
class CapitalPhasingAssumptions:
    """Controls how capital project spend is timed over the planning horizon."""

    planning_horizon_years: int = 10
    phasing_strategy: PhasingStrategy = PhasingStrategy.EVEN
    custom_phasing_weights: dict[int, float] = field(default_factory=dict)
    """Only used when phasing_strategy == CUSTOM. Maps year offset -> % of spend."""


@dataclass
class AssumptionSet:
    """Bundle of all assumption categories plus the projection start year."""

    start_year: int = 2026
    demand: DemandAssumptions = field(default_factory=DemandAssumptions)
    pricing: PricingAssumptions = field(default_factory=PricingAssumptions)
    operations: OperationalAssumptions = field(default_factory=OperationalAssumptions)
    inflation: InflationAssumptions = field(default_factory=InflationAssumptions)
    capital_phasing: CapitalPhasingAssumptions = field(
        default_factory=CapitalPhasingAssumptions
    )
