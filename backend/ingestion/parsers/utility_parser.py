import csv
import io
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

from emissions.models import EmissionRecord


REQUIRED_HEADERS = {
    "account_number",
    "meter_id",
    "site_name",
    "billing_period_start",
    "billing_period_end",
    "consumption_kwh",
    "demand_kw",
    "tariff_code",
    "cost_local_currency",
}

CONSUMPTION_PATTERN = re.compile(r"^\s*(?P<value>-?\d+(?:\.\d+)?)\s*(?P<unit>mwh|kwh)?\s*$", re.IGNORECASE)


class UtilityParserError(ValueError):
    """Raised when a utility electricity CSV cannot be parsed into records."""


def parse_utility_csv(file_obj, batch) -> list[EmissionRecord]:
    """
    Parse utility portal electricity exports into unsaved EmissionRecord objects.

    Consumption is normalized to kWh, billing periods are preserved as interval
    dates, and source meter/site context is stored in raw_payload for audit.
    """

    csv_text = _read_csv_text(file_obj)
    reader = csv.DictReader(io.StringIO(csv_text))
    if reader.fieldnames is None:
        return []

    missing_headers = sorted(REQUIRED_HEADERS - set(reader.fieldnames))
    if missing_headers:
        raise UtilityParserError(f"Missing required utility headers: {', '.join(missing_headers)}")

    records = []
    for row_number, row in enumerate(reader, start=2):
        period_start = _parse_iso_date(row["billing_period_start"])
        period_end = _parse_iso_date(row["billing_period_end"])
        consumption_value, source_unit = _parse_consumption(row["consumption_kwh"])
        consumption_kwh = consumption_value * Decimal("1000") if source_unit == "MWh" else consumption_value
        flag_reasons = []

        if (period_end - period_start).days + 1 > 45:
            flag_reasons.append("billing_period_exceeds_45_days")
        if consumption_kwh < 0:
            flag_reasons.append("negative_consumption")

        source_row_id = (
            f"{row['account_number']}:{row['meter_id']}:"
            f"{row['billing_period_start']}:{row['billing_period_end']}"
        )
        records.append(
            EmissionRecord(
                client=batch.data_source.client,
                data_source=batch.data_source,
                batch=batch,
                scope=EmissionRecord.Scope.SCOPE_2,
                activity_date=period_end,
                period_start=period_start,
                period_end=period_end,
                activity_type="grid_electricity",
                raw_value=consumption_kwh,
                raw_unit="kWh",
                normalized_value_kwh=consumption_kwh,
                co2e_kg=None,
                emission_factor_used="",
                source_row_id=source_row_id,
                raw_payload={
                    "original_row": row,
                    "row_number": row_number,
                    "account_number": row["account_number"],
                    "meter_id": row["meter_id"],
                    "site_name": row["site_name"],
                    "source_consumption": row["consumption_kwh"],
                    "source_consumption_unit": source_unit,
                    "demand_kw": row["demand_kw"],
                    "tariff_code": row["tariff_code"],
                    "cost_local_currency": row["cost_local_currency"],
                },
                status=(
                    EmissionRecord.Status.FLAGGED
                    if flag_reasons
                    else EmissionRecord.Status.PENDING_REVIEW
                ),
                flag_reason="; ".join(flag_reasons),
            )
        )

    return records


def _read_csv_text(file_obj) -> str:
    content = file_obj.read()
    if isinstance(content, bytes):
        return content.decode("utf-8-sig")
    return content


def _parse_iso_date(value: str):
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").date()
    except ValueError as exc:
        raise UtilityParserError(f"Invalid utility date value: {value}") from exc


def _parse_consumption(value: str) -> tuple[Decimal, str]:
    match = CONSUMPTION_PATTERN.match(value)
    if not match:
        raise UtilityParserError(f"Invalid consumption value: {value}")

    try:
        consumption = Decimal(match.group("value"))
    except InvalidOperation as exc:
        raise UtilityParserError(f"Invalid consumption value: {value}") from exc

    unit = (match.group("unit") or "kWh").lower()
    return consumption, "MWh" if unit == "mwh" else "kWh"
