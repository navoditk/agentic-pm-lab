"""Cross-repository agreement: this repo's analytics vs pm-mechanics.

pm-mechanics is the reference implementation for the maths both repositories
compute. These tests are the mechanism that keeps the two honest without
coupling them: `pm` is a test-time dependency only and is never imported by
shipped code, so the agent runtime does not inherit a teaching library's
release cycle.

Four functions genuinely duplicate across the two repositories. Each is
asserted to agree here. Everything else in `src/analytics` either has no
pm-mechanics counterpart (factor regression, backtesting, scenario shocks) or
differs by design, and is deliberately absent from this file.

Tolerances are stated per assertion rather than shared, because they mean
different things: a closed form reimplemented in two places should agree to
floating-point noise, while two different convex solvers should not be
expected to.
"""

import numpy as np
import pytest

from src.analytics.curves import interpolate_curve
from src.analytics.optimizer import optimize_portfolio
from src.analytics.pricers import black_scholes_price, price_bond
from src.analytics.risk import max_drawdown as lab_max_drawdown

pm = pytest.importorskip(
    "pm",
    reason="pm-mechanics is a dev-group dependency; install with `uv sync` to run agreement tests",
)

from pm.fixed_income.bond import bond_cashflows, bond_price
from pm.fixed_income.curve import interpolate_zero_rate
from pm.optimization import max_sharpe
from pm.options import black_scholes_call_price, black_scholes_put_price
from pm.returns import max_drawdown as pm_max_drawdown


def test_bond_price_matches_the_closed_form_on_a_flat_curve():
    """The paradigm difference between the two pricers is parameterisation only.

    This repo discounts explicit cash flows against a curve; pm-mechanics uses
    the closed-form YTM price. Those are the same computation whenever the
    curve is flat, because discounting every flow at one rate *is* the YTM
    formula. If this ever stops matching exactly, one of the two has changed
    its compounding or day handling.
    """
    ytm, face, coupon_rate, years, frequency = 0.04, 100.0, 0.05, 5.0, 2
    times, amounts = bond_cashflows(face, coupon_rate, years, frequency)
    flows = [
        {"time_years": float(t), "amount": float(a)}
        for t, a in zip(times, amounts, strict=True)
    ]
    flat_pct = ytm * 100  # this repo quotes curve rates in percent, pm in decimals

    ours = price_bond(
        flows, [0.5, 30.0], [flat_pct, flat_pct], compounding_frequency=frequency
    )
    theirs = bond_price(ytm, face, coupon_rate, years, frequency)

    # Exact: both reduce to the same sum of the same discount factors.
    assert ours["price"] == pytest.approx(theirs, abs=1e-12)


def test_bond_price_disagrees_on_a_sloped_curve_and_that_is_correct():
    """Guard against someone "fixing" the test above by making the curve
    irrelevant. On an upward-sloping curve the two must differ, because a
    single YTM cannot reproduce per-tenor discounting.
    """
    times, amounts = bond_cashflows(100.0, 0.05, 5.0, 2)
    flows = [
        {"time_years": float(t), "amount": float(a)}
        for t, a in zip(times, amounts, strict=True)
    ]
    sloped = price_bond(flows, [0.5, 10.0], [2.0, 6.0], compounding_frequency=2)[
        "price"
    ]
    flat = bond_price(0.04, 100.0, 0.05, 5.0, 2)
    assert sloped != pytest.approx(flat, abs=1e-6)


@pytest.mark.parametrize(
    ("option_type", "reference"),
    [("call", black_scholes_call_price), ("put", black_scholes_put_price)],
)
def test_black_scholes_matches(option_type, reference):
    """Same closed form, different call signatures.

    This repo takes an `option_type` argument and orders parameters
    (spot, strike, time, rate, vol); pm-mechanics splits call and put and
    orders them (spot, strike, rate, vol, time). The argument mapping below is
    the part worth pinning -- a silent reorder would still return a number.
    """
    spot, strike, time_to_expiry, rate, volatility = 100.0, 95.0, 1.0, 0.03, 0.2

    ours = black_scholes_price(
        spot, strike, time_to_expiry, rate, volatility, option_type
    )
    theirs = reference(spot, strike, rate, volatility, time_to_expiry)

    # Floating-point noise only: identical formula, identical inputs.
    assert ours["price"] == pytest.approx(theirs, abs=1e-10)


def test_curve_interpolation_matches():
    """This repo interpolates a list of tenors at once; pm-mechanics does one."""
    tenors = [1.0, 2.0, 5.0, 10.0]
    rates = [3.0, 3.4, 3.9, 4.2]
    targets = [1.5, 3.0, 7.5]

    ours = interpolate_curve(tenors, rates, targets)
    theirs = [interpolate_zero_rate(t, tenors, rates) for t in targets]

    assert ours == pytest.approx(theirs, abs=1e-12)


def test_max_sharpe_weights_agree_within_solver_tolerance():
    """Both maximise the same objective through different solvers.

    This repo delegates to PyPortfolioOpt; pm-mechanics uses cvxpy directly.
    Expecting bit-identical weights would be wrong, so the tolerance is loose
    on purpose -- 1e-4 is tight enough to catch a genuine formulation change
    (a missing constraint, a different risk-free handling) and loose enough to
    ignore solver noise.
    """
    assets = ["A", "B", "C"]
    expected_returns = {"A": 0.09, "B": 0.05, "C": 0.07}
    covariance = {
        "A": {"A": 0.040, "B": 0.006, "C": 0.010},
        "B": {"A": 0.006, "B": 0.020, "C": 0.004},
        "C": {"A": 0.010, "B": 0.004, "C": 0.030},
    }
    current = dict.fromkeys(assets, 1 / 3)

    ours = optimize_portfolio("max_sharpe", expected_returns, covariance, current)
    our_weights = [ours["weights"][a] for a in assets]

    theirs = max_sharpe(
        np.array([expected_returns[a] for a in assets]),
        np.array([[covariance[i][j] for j in assets] for i in assets]),
        risk_free_rate=0.0,
        long_only=True,
    )

    assert our_weights == pytest.approx([float(w) for w in theirs], abs=1e-4)


def test_the_two_max_drawdown_functions_take_different_inputs():
    """A tripwire, not an agreement check.

    Both repositories export `max_drawdown`. This repo's takes a series of
    portfolio *values*; pm-mechanics' takes a series of *returns*. Both accept
    a sequence of floats, so swapping them type-checks, runs, and returns a
    number.

    The failure is silent and severe: feeding values to the returns-based
    function reports **no drawdown at all**, because a series read as returns
    of +100, +110 ... only ever compounds upward. A risk number of zero is the
    worst possible wrong answer.
    """
    values = [100.0, 110.0, 88.0, 95.0, 120.0]

    ours = lab_max_drawdown(values)["max_drawdown"]
    misused = pm_max_drawdown(values)  # same list, read as returns

    assert ours == pytest.approx(-0.20, abs=1e-9)
    assert misused == pytest.approx(0.0, abs=1e-9)
    assert ours != pytest.approx(misused, abs=1e-6)


def test_max_drawdown_agrees_when_each_is_given_its_own_input():
    """The corollary: it is the same concept, only differently parameterised."""
    returns = [0.10, -0.20, 0.08, 0.26]
    values = list(np.cumprod([1 + r for r in returns]))

    theirs = pm_max_drawdown(returns)
    ours = lab_max_drawdown(values)["max_drawdown"]

    assert ours == pytest.approx(theirs, abs=1e-9)
