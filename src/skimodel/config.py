"""Global configuration constants and defaults."""

from __future__ import annotations

# Planning
DEFAULT_PLANNING_HORIZON_YEARS = 10
DEFAULT_START_YEAR = 2026

# Valuation
DEFAULT_DISCOUNT_RATE_PCT = 9.0
DEFAULT_TERMINAL_GROWTH_RATE_PCT = 2.0
DEFAULT_EV_EXIT_EBITDA_MULTIPLE = 7.0

# Simple placeholder effective tax rate applied to positive pre-tax cash flow.
DEFAULT_EFFECTIVE_TAX_RATE_PCT = 21.0

# Scenario naming conventions guaranteed to exist out of the box.
BASELINE_SCENARIO_NAME = "Baseline"
DEFAULT_SCENARIO_NAMES = ("Baseline", "Scenario A", "Scenario B", "Scenario C")

DEFAULT_CAPITAL_PROJECT_LIBRARY_PATH = "data/default_capital_projects.json"
