"""Delivery-time helper, using the per-zone table in rates.py."""
from rates import SHIPPING_DAYS


def delivery_days(zone, express=False):
    """Return the guaranteed delivery time in days for a zone (see
    rates.SHIPPING_DAYS). Express halves the time, rounded up."""
    days = SHIPPING_DAYS[zone]
    if express:
        return (days + 1) // 2
    return days
