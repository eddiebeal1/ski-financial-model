"""Tabular multi-scenario comparison helpers."""

from __future__ import annotations

import pandas as pd

from skimodel.projection.results import ProjectionResults


def compare_scenarios(results_by_name: dict[str, ProjectionResults]) -> pd.DataFrame:
    """Return a tidy one-row-per-scenario summary table for side-by-side review."""

    rows = []
    for name, results in results_by_name.items():
        rows.append(
            {
                "Scenario": name,
                "Revenue CAGR %": results.revenue_cagr_pct(),
                "Avg EBITDA Margin %": (
                    sum(results.ebitda_margin_pct()) / len(results.ebitda_margin_pct())
                    if results.ebitda_margin_pct()
                    else 0.0
                ),
                "Total Capital Cost": results.total_capital_cost,
                "Funding Gap": results.funding_gap,
                "NPV": results.npv,
                "IRR %": results.irr,
                "Enterprise Value": results.enterprise_value,
            }
        )
    return pd.DataFrame(rows).set_index("Scenario")
