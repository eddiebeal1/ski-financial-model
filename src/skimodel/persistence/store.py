"""Session-state wrapper + JSON import/export for the whole workbook.

Keeps Streamlit-specific state access (``st.session_state``) isolated to this module so
the rest of ``skimodel`` stays framework-agnostic.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Any

from skimodel.capital_projects.library import CapitalProjectLibrary
from skimodel.config import DEFAULT_CAPITAL_PROJECT_LIBRARY_PATH, DEFAULT_SCENARIO_NAMES
from skimodel.scenarios.manager import ScenarioManager

_LIBRARY_KEY = "skimodel_project_library"
_SCENARIO_MANAGER_KEY = "skimodel_scenario_manager"


class SessionStore:
    """Facade over ``st.session_state`` providing the two shared singletons.

    A ``session_state``-like mapping is injected so this class can be unit tested
    without importing Streamlit (a plain dict satisfies the same interface).
    """

    def __init__(self, session_state: Any) -> None:
        self._state = session_state
        self._bootstrap()

    def _bootstrap(self) -> None:
        if _LIBRARY_KEY not in self._state:
            library = CapitalProjectLibrary()
            library.load_defaults(DEFAULT_CAPITAL_PROJECT_LIBRARY_PATH)
            self._state[_LIBRARY_KEY] = library

        if _SCENARIO_MANAGER_KEY not in self._state:
            manager = ScenarioManager()
            for name in DEFAULT_SCENARIO_NAMES:
                manager.create_scenario(name=name)
            self._state[_SCENARIO_MANAGER_KEY] = manager

    @property
    def project_library(self) -> CapitalProjectLibrary:
        return self._state[_LIBRARY_KEY]

    @property
    def scenario_manager(self) -> ScenarioManager:
        return self._state[_SCENARIO_MANAGER_KEY]

    # -- Export / import (closest analog to Excel "Save As") -----------------------
    def export_json(self) -> str:
        payload = {
            "project_library": [
                dataclasses.asdict(p) for p in self.project_library.list_projects()
            ],
            "scenarios": [
                dataclasses.asdict(s) for s in self.scenario_manager.list_scenarios()
            ],
        }
        return json.dumps(payload, indent=2, default=str)

    def export_to_file(self, path: str | Path) -> None:
        Path(path).write_text(self.export_json(), encoding="utf-8")
