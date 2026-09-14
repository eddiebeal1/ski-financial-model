"""KPI card data preparation for the Executive Dashboard."""

from __future__ import annotations

from typing import TypedDict

from skimodel.projection.results import ProjectionResults


class KpiCard(TypedDict):
    label: str
    value: str
    help_text: str


def _fmt_currency(value: float) -> str:
    return f"${value:,.0f}"


def _fmt_pct(value: float) -> str:
    return f"{value:,.1f}%"


def build_kpi_cards(results: ProjectionResults) -> list[KpiCard]:
    """Return the standard set of executive KPI cards for a projection result."""

    avg_margin = (
        sum(results.ebitda_margin_pct()) / len(results.ebitda_margin_pct())
        if results.ebitda_margin_pct()
        else 0.0
    )
    irr_display = _fmt_pct(results.irr) if results.irr is not None else "n/a"

    return [
        KpiCard(
            label="Revenue CAGR",
            value=_fmt_pct(results.revenue_cagr_pct()),
            help_text="Compound annual growth rate of revenue over the planning horizon.",
        ),
        KpiCard(
            label="Avg. EBITDA Margin",
            value=_fmt_pct(avg_margin),
            help_text="Average EBITDA as a % of revenue across the horizon.",
        ),
        KpiCard(
            label="NPV of Free Cash Flow",
            value=_fmt_currency(results.npv),
            help_text="Net present value of projected free cash flow at the chosen discount rate.",
        ),
        KpiCard(
            label="IRR",
            value=irr_display,
            help_text="Internal rate of return implied by the free cash flow stream.",
        ),
        KpiCard(
            label="Enterprise Value",
            value=_fmt_currency(results.enterprise_value),
            help_text="PV of free cash flow plus discounted terminal value.",
        ),
        KpiCard(
            label="Funding Gap",
            value=_fmt_currency(results.funding_gap),
            help_text="Capital cost not yet covered by debt, equity, or grants (negative = surplus).",
        ),
    ]
