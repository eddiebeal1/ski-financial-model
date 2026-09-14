"""Scenario data model."""

from __future__ import annotations

import copy
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from skimodel.assumptions.defaults import default_assumption_set
from skimodel.assumptions.models import AssumptionSet
from skimodel.capital_projects.models import CapitalProject
from skimodel.capital_stack.models import CapitalStructure


@dataclass
class Scenario:
    """A named, self-contained strategic alternative.

    Holds its own copies of assumptions, selected capital projects, and capital
    structure so that editing the shared project library or another scenario never
    silently mutates this one.
    """

    name: str
    description: str = ""
    assumption_set: AssumptionSet = field(default_factory=default_assumption_set)
    selected_projects: list[CapitalProject] = field(default_factory=list)
    capital_structure: CapitalStructure = field(default_factory=CapitalStructure)
    is_baseline: bool = False
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def total_capital_cost(self) -> float:
        return sum(p.total_cost for p in self.selected_projects if p.is_active)

    def clone(self, new_name: str) -> "Scenario":
        """Deep-copy this scenario under a new name/id, unflagged as baseline."""

        clone = copy.deepcopy(self)
        clone.id = str(uuid.uuid4())
        clone.name = new_name
        clone.is_baseline = False
        clone.created_at = datetime.now(timezone.utc).isoformat()
        return clone
