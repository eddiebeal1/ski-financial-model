"""Factory functions producing default assumption sets (e.g. for the Baseline scenario)."""

from __future__ import annotations

from skimodel.assumptions.models import AssumptionSet


def default_assumption_set() -> AssumptionSet:
    """Return a fresh AssumptionSet populated with reasonable industry defaults.

    A fresh instance is returned on every call so callers (e.g. cloning a scenario)
    never accidentally share mutable state.
    """

    return AssumptionSet()
