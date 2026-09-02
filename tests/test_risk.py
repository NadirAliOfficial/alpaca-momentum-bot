import pytest

from src.risk import atr_stop, size_position


def test_risk_amount_and_even_quantity():
    plan = size_position(100_000, 0.01, entry=100.0, stop=98.0, reward_risk=2.5)
    assert plan.risk_amount == 1_000.0
    assert plan.per_share_risk == 2.0
    assert plan.quantity == 500          # 1000 / 2, already even
    assert plan.quantity % 2 == 0
    assert plan.total_risk == 1_000.0


def test_quantity_floored_to_even():
    # 1000 / 3 = 333.33 -> floor 333 -> even floor 332
    plan = size_position(100_000, 0.01, entry=100.0, stop=97.0)
    assert plan.quantity == 332


def test_target_uses_reward_risk_multiple():
    plan = size_position(100_000, 0.01, entry=100.0, stop=96.0, reward_risk=2.0)
    assert plan.target == 108.0          # 100 + 4 * 2.0
    assert plan.reward_risk == 2.0


def test_small_budget_is_untradeable():
    plan = size_position(300, 0.01, entry=100.0, stop=98.0)
    assert plan.quantity == 0
    assert plan.tradeable is False


def test_stop_must_be_below_entry():
    with pytest.raises(ValueError):
        size_position(100_000, 0.01, entry=100.0, stop=100.0)


def test_atr_stop_helper():
    assert atr_stop(100.0, 2.0, mult=1.5) == 97.0
