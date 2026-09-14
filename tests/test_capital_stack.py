from skimodel.capital_stack.analyzer import CapitalStackAnalyzer
from skimodel.capital_stack.models import (
    AmortizationType,
    CapitalStructure,
    DebtTranche,
    EquityTranche,
    Grant,
)


def test_amortizing_schedule_pays_off_balance():
    tranche = DebtTranche(name="Loan", principal=1_000_000, interest_rate_pct=5.0, term_years=10)
    schedule = CapitalStackAnalyzer.build_debt_schedule(tranche)
    assert len(schedule) == 10
    assert abs(schedule.iloc[-1]["ending_balance"]) < 1e-6


def test_interest_only_schedule_keeps_principal_flat():
    tranche = DebtTranche(
        name="IO Loan", principal=1_000_000, interest_rate_pct=5.0, term_years=5,
        amortization_type=AmortizationType.INTEREST_ONLY,
    )
    schedule = CapitalStackAnalyzer.build_debt_schedule(tranche)
    assert (schedule["principal_payment"] == 0).all()
    assert schedule.iloc[-1]["ending_balance"] == 1_000_000


def test_bullet_schedule_repays_at_final_year():
    tranche = DebtTranche(
        name="Bullet Loan", principal=500_000, interest_rate_pct=6.0, term_years=3,
        amortization_type=AmortizationType.BULLET,
    )
    schedule = CapitalStackAnalyzer.build_debt_schedule(tranche)
    assert schedule.iloc[-1]["principal_payment"] == 500_000
    assert schedule.iloc[-1]["ending_balance"] == 0


def test_funding_gap_calculation():
    structure = CapitalStructure(
        debt_tranches=[DebtTranche(name="Loan", principal=1_000_000, interest_rate_pct=5.0, term_years=5)],
        equity_tranches=[EquityTranche(name="Equity", amount=500_000, required_return_pct=15.0)],
        grants=[Grant(name="Grant", amount=250_000)],
    )
    gap = CapitalStackAnalyzer.compute_funding_gap(structure, total_project_cost=2_000_000)
    assert gap == 250_000


def test_blended_cost_of_capital():
    structure = CapitalStructure(
        debt_tranches=[DebtTranche(name="Loan", principal=1_000_000, interest_rate_pct=5.0, term_years=5)],
        equity_tranches=[EquityTranche(name="Equity", amount=1_000_000, required_return_pct=15.0)],
    )
    blended = CapitalStackAnalyzer.blended_cost_of_capital(structure)
    assert blended == 10.0  # (5% * 1M + 15% * 1M) / 2M
