"""Observed costs are comparable only when their declared units agree."""
from .state import UNKNOWN

OBSERVED_COST = "OBSERVED_COST"
CONFIGURED_LIMIT = "CONFIGURED_LIMIT"


def validate_cost_semantics(semantics: str, unit: str) -> None:
    if semantics not in {OBSERVED_COST, CONFIGURED_LIMIT, UNKNOWN}:
        raise ValueError("unsupported cost_semantics")
    if not isinstance(unit, str) or not unit.strip():
        raise ValueError("cost_unit must be explicit or UNKNOWN")


def observed_cost(records):
    rows = [row for row in records
            if row.cost_semantics == OBSERVED_COST and row.cost_unit != UNKNOWN]
    units = {row.cost_unit for row in rows}
    if len(units) > 1:
        raise ValueError("INCOMPATIBLE_COST_UNITS")
    # Divide before summing to avoid overflowing a finite mean.
    mean = sum(row.cost / len(rows) for row in rows) if rows else 0.0
    return mean, len(rows), next(iter(units), UNKNOWN)
