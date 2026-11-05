from decimal import Decimal, ROUND_HALF_UP

STAGE_PROBABILITY = {
    "Prospecting": 10, "Qualification": 25, "Needs Analysis": 40,
    "Proposal": 60, "Negotiation": 80, "Closed Won": 100, "Closed Lost": 0,
}
APPROVAL_DISCOUNT_PERCENT = 15

def money(value: object) -> float:
    """Round commercial values using decimal, never binary float arithmetic."""
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

def requires_approval(discount_percent: float) -> bool:
    return Decimal(str(discount_percent)) > Decimal(APPROVAL_DISCOUNT_PERCENT)

