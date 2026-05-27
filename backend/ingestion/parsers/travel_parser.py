import json
from datetime import datetime
from decimal import Decimal, InvalidOperation

from emissions.models import EmissionRecord
from ingestion.utils.emission_factors import DEFRA_2023_TRAVEL_FACTORS


FLIGHT_ACTIVITY_BY_CLASS = {
    "economy": "flight_economy",
    "business": "flight_business",
    "first": "flight_first",
}

CATEGORY_ACTIVITY = {
    "hotel": "hotel_stay",
    "car": "car_rental",
    "rail": "rail_travel",
}


class TravelParserError(ValueError):
    """Raised when a travel JSON export cannot be parsed into records."""


def parse_travel_json(file_obj, batch) -> list[EmissionRecord]:
    """
    Parse Concur/Navan-style travel expense JSON into unsaved EmissionRecords.

    All travel categories are Scope 3. CO2e is calculated when the relevant
    activity amount is available; flights without distance are flagged but still
    returned so downstream review can estimate the route.
    """

    expenses = _read_json(file_obj)
    if not isinstance(expenses, list):
        raise TravelParserError("Travel export must be a JSON array of expenses")

    records = []
    for row_number, expense in enumerate(expenses, start=1):
        trip_date = _parse_iso_date(expense["trip_date"])
        activity_type = _activity_type_for_expense(expense)
        raw_value, raw_unit = _activity_amount(expense, activity_type)
        flag_reason = ""
        if activity_type.startswith("flight_") and raw_value is None:
            flag_reason = "missing_distance_estimate_required"

        co2e_kg, factor_label = _calculate_co2e(activity_type, raw_value)

        records.append(
            EmissionRecord(
                client=batch.data_source.client,
                data_source=batch.data_source,
                batch=batch,
                scope=EmissionRecord.Scope.SCOPE_3,
                activity_date=trip_date,
                period_start=trip_date,
                period_end=trip_date,
                activity_type=activity_type,
                raw_value=raw_value or Decimal("0"),
                raw_unit=raw_unit,
                normalized_value_kwh=None,
                co2e_kg=co2e_kg,
                emission_factor_used=factor_label,
                source_row_id=expense["expense_id"],
                raw_payload={
                    "original_record": expense,
                    "row_number": row_number,
                    "employee_id": expense.get("employee_id"),
                    "category": expense.get("category"),
                    "vendor": expense.get("vendor"),
                    "origin": expense.get("origin"),
                    "destination": expense.get("destination"),
                    "distance_km": expense.get("distance_km"),
                    "cost_usd": expense.get("cost_usd"),
                    "nights": expense.get("nights"),
                    "flight_class": expense.get("flight_class"),
                },
                status=(
                    EmissionRecord.Status.FLAGGED
                    if flag_reason
                    else EmissionRecord.Status.PENDING_REVIEW
                ),
                flag_reason=flag_reason,
            )
        )

    return records


def _read_json(file_obj):
    content = file_obj.read()
    if isinstance(content, bytes):
        content = content.decode("utf-8-sig")
    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise TravelParserError("Invalid travel JSON export") from exc


def _parse_iso_date(value: str):
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").date()
    except ValueError as exc:
        raise TravelParserError(f"Invalid travel date value: {value}") from exc


def _activity_type_for_expense(expense: dict) -> str:
    category = expense.get("category", "").strip().lower()
    if category == "air":
        flight_class = expense.get("flight_class") or "Economy"
        return FLIGHT_ACTIVITY_BY_CLASS.get(flight_class.strip().lower(), "flight_economy")
    if category in CATEGORY_ACTIVITY:
        return CATEGORY_ACTIVITY[category]
    raise TravelParserError(f"Unsupported travel category: {expense.get('category')}")


def _activity_amount(expense: dict, activity_type: str) -> tuple[Decimal | None, str]:
    if activity_type.startswith("flight_") or activity_type in {"car_rental", "rail_travel"}:
        distance = expense.get("distance_km")
        return (_to_decimal(distance), "km") if distance is not None else (None, "km")
    if activity_type == "hotel_stay":
        return _to_decimal(expense.get("nights") or 0), "nights"
    return Decimal("0"), "unit"


def _calculate_co2e(activity_type: str, raw_value: Decimal | None) -> tuple[Decimal | None, str]:
    factor = DEFRA_2023_TRAVEL_FACTORS.get(activity_type)
    if factor is None:
        return None, ""
    if raw_value is None:
        return None, factor["label"]
    return raw_value * factor["factor"], factor["label"]


def _to_decimal(value) -> Decimal:
    try:
        return Decimal(str(value))
    except InvalidOperation as exc:
        raise TravelParserError(f"Invalid numeric travel value: {value}") from exc
