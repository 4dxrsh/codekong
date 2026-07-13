"""Billing helpers. Every rate lives in rates.py; the docstrings describe
behaviour, not the specific numbers — read rates.py for those."""
from rates import (TAX_RATES, SHIPPING, DISCOUNTS, FX_TO_USD, BULK_BREAKS,
                   PRIORITY_SURCHARGE, LATE_FEE_PCT, LATE_FEE_GRACE_DAYS)


def price_with_tax(amount, category):
    """Return amount plus its category's sales tax, rounded to cents.
    The rate depends on the product category (see rates.TAX_RATES)."""
    return round(amount * (1 + TAX_RATES[category]), 2)


def shipping_total(subtotal, zone, free_over=100.0):
    """Add the zone's flat shipping fee to subtotal, waiving it when the
    subtotal is at or above free_over. Rounded to cents."""
    fee = 0.0 if subtotal >= free_over else SHIPPING[zone]
    return round(subtotal + fee, 2)


def member_price(amount, tier):
    """Apply the member tier's loyalty discount to amount, rounded to cents.
    Higher tiers get a larger discount (see rates.DISCOUNTS)."""
    return round(amount * (1 - DISCOUNTS[tier]), 2)


def to_usd(amount, currency):
    """Convert an amount in the given currency to US dollars, rounded to cents,
    using the exchange rates in rates.FX_TO_USD."""
    return round(amount * FX_TO_USD[currency], 2)


def bulk_discount(quantity):
    """Return the bulk discount fraction earned for ordering `quantity` units,
    per the volume breakpoints in rates.BULK_BREAKS."""
    for min_qty, frac in BULK_BREAKS:
        if quantity >= min_qty:
            return frac
    return 0.0


def priority_price(amount):
    """Return amount plus the flat priority-handling surcharge, rounded to
    cents (surcharge fraction in rates.PRIORITY_SURCHARGE)."""
    return round(amount * (1 + PRIORITY_SURCHARGE), 2)


def late_fee(balance, days_overdue):
    """Return the late fee on an overdue balance: nothing during the grace
    period, then a flat fraction of the balance once it is passed."""
    if days_overdue <= LATE_FEE_GRACE_DAYS:
        return 0.0
    return round(balance * LATE_FEE_PCT, 2)


def checkout_total(amount, category, tier):
    """Full checkout price: apply the category's tax, then the member tier's
    discount, in that order. Rounded to cents."""
    taxed = price_with_tax(amount, category)
    return member_price(taxed, tier)
