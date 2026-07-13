"""Reference tables for the billing/grading/shipping utilities — the single
source of truth for every rate, threshold and lookup table. Values are
domain-specific and intentionally non-standard; you cannot guess them."""

# Sales-tax rate charged per product category.
TAX_RATES = {"food": 0.055, "standard": 0.175, "luxury": 0.31, "digital": 0.09}

# Flat shipping fee (dollars) charged per delivery zone.
SHIPPING = {"local": 3.0, "regional": 8.5, "national": 14.0, "international": 32.0}

# Guaranteed delivery time (days) per delivery zone.
SHIPPING_DAYS = {"local": 1, "regional": 3, "national": 6, "international": 11}

# Loyalty discount fraction granted per membership tier.
DISCOUNTS = {"bronze": 0.0, "silver": 0.07, "gold": 0.14, "platinum": 0.22}

# Exchange rate to USD for each supported currency code.
FX_TO_USD = {"USD": 1.0, "EUR": 1.09, "GBP": 1.27, "JPY": 0.0067, "INR": 0.012}

# Bulk order discount: (minimum quantity, discount fraction), highest first.
BULK_BREAKS = [(100, 0.18), (50, 0.11), (10, 0.04), (0, 0.0)]

# Extra fraction charged for priority handling.
PRIORITY_SURCHARGE = 0.35

# Minimum score (inclusive) for each letter grade, highest band first.
# NOTE: non-standard cutoffs (not 90/80/70/60).
GRADE_BANDS = [(88, "A"), (76, "B"), (64, "C"), (52, "D"), (0, "F")]

# Lowest passing score, and the GPA at/above which a student makes honor roll.
PASS_MARK = 52
HONOR_GPA = 3.6

# Late fee: fraction of the balance charged once an invoice passes the grace period.
LATE_FEE_PCT = 0.015
LATE_FEE_GRACE_DAYS = 30
