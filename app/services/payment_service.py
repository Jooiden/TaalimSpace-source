from decimal import Decimal, ROUND_HALF_UP


def calculate_shares(amount: Decimal) -> tuple[Decimal, Decimal]:
    """Для MVP в KGS: комиссия 10%, остаток преподавателю, точность 0.01."""
    if not amount.is_finite() or amount < 0 or amount != amount.quantize(Decimal("0.01")):
        raise ValueError("Amount must be non-negative with at most two decimal places")
    commission = (amount * Decimal("0.10")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return commission, amount - commission
