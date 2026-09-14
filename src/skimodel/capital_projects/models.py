"""Capital project catalog data model."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum


class ProjectCategory(str, Enum):
    LIFT = "lift"
    SNOWMAKING = "snowmaking"
    LODGE = "lodge"
    BASE_AREA = "base_area"
    TERRAIN = "terrain"
    INFRASTRUCTURE = "infrastructure"
    TECHNOLOGY = "technology"
    LODGING = "lodging"
    OTHER = "other"


@dataclass
class CapitalProject:
    """A single predefined or user-added capital investment.

    ``start_year_offset`` and ``duration_years`` express timing relative to the
    projection start year rather than absolute calendar years, so a project's timing
    can be re-assigned per scenario without mutating the shared library entry.
    """

    name: str
    category: ProjectCategory = ProjectCategory.OTHER
    total_cost: float = 0.0
    start_year_offset: int = 0
    """Years after projection start (year 0 = first projection year) when spend begins."""
    duration_years: int = 1
    expected_annual_revenue_impact: float = 0.0
    """Incremental annual revenue once the project is online (year over year)."""
    expected_annual_opex_impact: float = 0.0
    """Incremental annual opex once the project is online (can be negative for savings)."""
    useful_life_years: int = 15
    is_active: bool = True
    description: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def annual_spend_schedule(self) -> dict[int, float]:
        """Even spend across the project's duration, keyed by year offset."""

        if self.duration_years <= 0:
            return {self.start_year_offset: self.total_cost}
        per_year = self.total_cost / self.duration_years
        return {
            self.start_year_offset + i: per_year for i in range(self.duration_years)
        }

    def online_year_offset(self) -> int:
        """First year offset in which the project's operating impact applies."""

        return self.start_year_offset + self.duration_years
