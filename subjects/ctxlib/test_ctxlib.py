"""Existing (intentionally shallow) suite — the baseline the mutation study
measures against. Each test checks only a trivial / identity case that does NOT
reveal a non-trivial constant, so bugs affecting other categories/zones/tiers/
bands survive and become the targets the LLM must write new tests to kill."""
from billing import (price_with_tax, shipping_total, member_price, to_usd,
                     bulk_discount, priority_price, late_fee, checkout_total)
from shipping import delivery_days
from grading import letter_grade, gpa_points, is_passing, is_honor_roll


def test_price_with_tax_standard():
    assert price_with_tax(100.0, "standard") == 117.5


def test_shipping_waived_over_threshold():
    assert shipping_total(150.0, "local") == 150.0


def test_member_price_bronze_identity():
    assert member_price(100.0, "bronze") == 100.0


def test_to_usd_identity():
    assert to_usd(100.0, "USD") == 100.0


def test_bulk_discount_below_first_break():
    assert bulk_discount(5) == 0.0


def test_late_fee_within_grace():
    assert late_fee(1000.0, 10) == 0.0


def test_checkout_total_standard_bronze():
    assert checkout_total(100.0, "standard", "bronze") == 117.5


def test_letter_grade_top():
    assert letter_grade(95) == "A"


def test_gpa_points_top():
    assert gpa_points(95) == 4.0
