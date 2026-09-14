"""CRUD catalog for capital projects."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from skimodel.capital_projects.models import CapitalProject, ProjectCategory


class ProjectNotFoundError(KeyError):
    """Raised when a project id does not exist in the library."""


class CapitalProjectLibrary:
    """In-memory catalog of capital projects with CRUD + timing/cost assignment.

    Scenarios reference projects **by id**; editing the shared library does not
    retroactively alter a scenario's already-selected snapshot because
    ``Scenario`` stores its own copies at selection time (see ``scenarios.manager``).
    """

    def __init__(self) -> None:
        self._projects: dict[str, CapitalProject] = {}

    # -- CRUD -----------------------------------------------------------------
    def add_project(self, project: CapitalProject) -> CapitalProject:
        self._projects[project.id] = project
        return project

    def remove_project(self, project_id: str) -> None:
        self._projects.pop(project_id, None)

    def update_project(self, project_id: str, **updates: object) -> CapitalProject:
        project = self.get_project(project_id)
        for key, value in updates.items():
            if not hasattr(project, key):
                raise AttributeError(f"CapitalProject has no field '{key}'")
            setattr(project, key, value)
        return project

    def get_project(self, project_id: str) -> CapitalProject:
        try:
            return self._projects[project_id]
        except KeyError as exc:
            raise ProjectNotFoundError(project_id) from exc

    def list_projects(self, active_only: bool = False) -> list[CapitalProject]:
        projects = list(self._projects.values())
        if active_only:
            projects = [p for p in projects if p.is_active]
        return sorted(projects, key=lambda p: p.start_year_offset)

    # -- Timing / cost assignment ---------------------------------------------
    def assign_timing(
        self, project_id: str, start_year_offset: int, duration_years: int
    ) -> CapitalProject:
        return self.update_project(
            project_id,
            start_year_offset=start_year_offset,
            duration_years=duration_years,
        )

    def assign_cost(self, project_id: str, total_cost: float) -> CapitalProject:
        return self.update_project(project_id, total_cost=total_cost)

    # -- Seeding / export -------------------------------------------------------
    def load_defaults(self, path: str | Path = "data/default_capital_projects.json") -> None:
        """Populate the library from the seed JSON catalog, replacing current contents."""

        data = json.loads(Path(path).read_text(encoding="utf-8"))
        self._projects.clear()
        for entry in data:
            entry = dict(entry)
            entry["category"] = ProjectCategory(entry.get("category", "other"))
            self.add_project(CapitalProject(**entry))

    def to_dataframe(self) -> pd.DataFrame:
        rows = [
            {
                "id": p.id,
                "name": p.name,
                "category": p.category.value,
                "total_cost": p.total_cost,
                "start_year_offset": p.start_year_offset,
                "duration_years": p.duration_years,
                "expected_annual_revenue_impact": p.expected_annual_revenue_impact,
                "expected_annual_opex_impact": p.expected_annual_opex_impact,
                "useful_life_years": p.useful_life_years,
                "is_active": p.is_active,
            }
            for p in self.list_projects()
        ]
        return pd.DataFrame(rows)
