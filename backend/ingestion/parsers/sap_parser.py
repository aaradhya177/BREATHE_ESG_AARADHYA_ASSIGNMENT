import csv
import io
from datetime import datetime
from decimal import Decimal, InvalidOperation

from emissions.models import EmissionRecord


HEADER_MAP = {
    "Belegnummer": "source_row_id",
    "Buchungsdatum": "activity_date",
    "Werk": "plant_code",
    "Materialnummer": "material_code",
    "Materialkurztext": "material_description",
    "Menge": "quantity",
    "Mengeneinheit": "unit",
    "Kostenstelle": "cost_center",
}

FACILITY_BY_PLANT = {
    "1000": "Berlin Manufacturing Plant",
    "2000": "Hamburg Processing Plant",
    "3000": "Munich Logistics Depot",
}

ACTIVITY_TYPE_BY_MATERIAL = {
    "DIESEL-001": "diesel_combustion",
    "NATGAS-002": "natural_gas_combustion",
    "HFO-003": "heating_oil_combustion",
}

LIQUID_MATERIALS = {"DIESEL-001", "HFO-003"}
GAS_MATERIALS = {"NATGAS-002"}

LITERS_PER_GALLON = Decimal("3.785411784")
KG_PER_TONNE = Decimal("1000")
LIQUID_DENSITY_KG_PER_LITER = {
    "DIESEL-001": Decimal("0.832"),
    "HFO-003": Decimal("0.960"),
}
NATURAL_GAS_DENSITY_KG_PER_M3 = Decimal("0.717")


class SapFuelParserError(ValueError):
    """Raised when an SAP fuel CSV cannot be parsed into emission records."""


def parse_sap_fuel_csv(file_obj, batch) -> list[EmissionRecord]:
    """
    Parse a semicolon-delimited SAP fuel export into unsaved EmissionRecord objects.

    The parser accepts German SAP-style headers, DD.MM.YYYY dates, and European
    decimal numbers. It normalizes liquid fuels to liters and natural gas to m3.
    Rows with zero quantity or an unrecognized unit are returned as flagged
    records so callers can still bulk-create a complete audit trail.
    """

    csv_text = _read_csv_text(file_obj)
    reader = csv.DictReader(io.StringIO(csv_text), delimiter=";")
    if reader.fieldnames is None:
        return []

    missing_headers = sorted(set(HEADER_MAP) - set(reader.fieldnames))
    if missing_headers:
        raise SapFuelParserError(f"Missing required SAP headers: {', '.join(missing_headers)}")

    records = []
    for row_number, row in enumerate(reader, start=2):
        internal_row = _map_row(row)
        activity_date = _parse_sap_date(internal_row["activity_date"])
        source_quantity = _parse_european_decimal(internal_row["quantity"])
        material_code = internal_row["material_code"].strip().upper()
        source_unit = internal_row["unit"].strip().upper()
        activity_type = ACTIVITY_TYPE_BY_MATERIAL.get(material_code, "unknown_fuel_combustion")

        converted_quantity, base_unit, unit_flag = _convert_to_base_unit(
            source_quantity,
            source_unit,
            material_code,
        )
        flag_reasons = []
        if source_quantity == 0:
            flag_reasons.append("Quantity is zero")
        if unit_flag:
            flag_reasons.append(unit_flag)

        raw_payload = {
            "original_row": row,
            "mapped_row": internal_row,
            "row_number": row_number,
            "facility_name": FACILITY_BY_PLANT.get(internal_row["plant_code"], "Unknown facility"),
            "source_quantity": str(source_quantity),
            "source_unit": source_unit,
            "base_unit": base_unit,
        }

        records.append(
            EmissionRecord(
                client=batch.data_source.client,
                data_source=batch.data_source,
                batch=batch,
                scope=EmissionRecord.Scope.SCOPE_1,
                activity_date=activity_date,
                period_start=activity_date,
                period_end=activity_date,
                activity_type=activity_type,
                raw_value=converted_quantity,
                raw_unit=base_unit,
                normalized_value_kwh=None,
                co2e_kg=None,
                emission_factor_used="",
                source_row_id=internal_row["source_row_id"] or f"row-{row_number}",
                raw_payload=raw_payload,
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


def _map_row(row: dict[str, str]) -> dict[str, str]:
    return {internal_name: row.get(sap_name, "") for sap_name, internal_name in HEADER_MAP.items()}


def _parse_european_decimal(value: str) -> Decimal:
    normalized = value.strip().replace(".", "").replace(",", ".")
    try:
        return Decimal(normalized)
    except InvalidOperation as exc:
        raise SapFuelParserError(f"Invalid European decimal value: {value}") from exc


def _parse_sap_date(value: str):
    try:
        return datetime.strptime(value.strip(), "%d.%m.%Y").date()
    except ValueError as exc:
        raise SapFuelParserError(f"Invalid SAP date value: {value}") from exc


def _convert_to_base_unit(quantity: Decimal, unit: str, material_code: str) -> tuple[Decimal, str, str]:
    if material_code in GAS_MATERIALS:
        return _convert_gas_to_m3(quantity, unit)
    if material_code in LIQUID_MATERIALS:
        return _convert_liquid_to_liters(quantity, unit, material_code)
    return quantity, unit or "UNKNOWN", f"Unknown material code: {material_code}"


def _convert_liquid_to_liters(quantity: Decimal, unit: str, material_code: str) -> tuple[Decimal, str, str]:
    density = LIQUID_DENSITY_KG_PER_LITER[material_code]
    if unit == "L":
        return quantity, "L", ""
    if unit == "GAL":
        return quantity * LITERS_PER_GALLON, "L", ""
    if unit == "KG":
        return quantity / density, "L", ""
    if unit == "TO":
        return (quantity * KG_PER_TONNE) / density, "L", ""
    return quantity, unit or "UNKNOWN", f"Unrecognized unit for liquid fuel: {unit or 'blank'}"


def _convert_gas_to_m3(quantity: Decimal, unit: str) -> tuple[Decimal, str, str]:
    if unit == "M3":
        return quantity, "M3", ""
    if unit == "KG":
        return quantity / NATURAL_GAS_DENSITY_KG_PER_M3, "M3", ""
    if unit == "TO":
        return (quantity * KG_PER_TONNE) / NATURAL_GAS_DENSITY_KG_PER_M3, "M3", ""
    return quantity, unit or "UNKNOWN", f"Unrecognized unit for natural gas: {unit or 'blank'}"
