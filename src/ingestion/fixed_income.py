"""Validation helpers for the learning-scale fixed-income instrument master."""

from typing import Any

REQUIRED_BOND_FIELDS = {
    "security_id",
    "issuer",
    "currency",
    "issue_date",
    "maturity_date",
    "coupon_rate",
    "coupon_frequency",
    "day_count",
    "settlement_lag_days",
}


def validate_bond_instrument(record: dict[str, Any]) -> dict[str, Any]:
    """Validate minimum bond terms before a deterministic calculation."""
    missing = sorted(REQUIRED_BOND_FIELDS.difference(record))
    if missing:
        return {
            "status": "needs_review",
            "missing_fields": missing,
            "reason": "bond terms are incomplete; no valuation is permitted",
        }
    if float(record["coupon_rate"]) < 0:
        return {"status": "needs_review", "reason": "coupon_rate cannot be negative"}
    if int(record["coupon_frequency"]) <= 0:
        return {
            "status": "needs_review",
            "reason": "coupon_frequency must be positive",
        }
    if int(record["settlement_lag_days"]) < 0:
        return {
            "status": "needs_review",
            "reason": "settlement_lag_days cannot be negative",
        }
    if str(record["maturity_date"]) <= str(record["issue_date"]):
        return {
            "status": "needs_review",
            "reason": "maturity_date must follow issue_date",
        }
    return {"status": "valid", "security_id": str(record["security_id"])}
