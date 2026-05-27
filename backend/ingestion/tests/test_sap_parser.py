from decimal import Decimal
from io import StringIO

from django.core.files.base import ContentFile
from django.test import TestCase

from emissions.models import Client, DataSource, EmissionRecord, IngestionBatch
from ingestion.parsers.sap_parser import parse_sap_fuel_csv


CSV_HEADER = (
    "Belegnummer;Buchungsdatum;Werk;Materialnummer;Materialkurztext;"
    "Menge;Mengeneinheit;Kostenstelle\n"
)


class SapFuelParserTests(TestCase):
    def setUp(self):
        self.client_obj = Client.objects.create(name="Acme Corp", slug="acme-corp")
        self.data_source = DataSource.objects.create(
            client=self.client_obj,
            source_type=DataSource.SourceType.SAP_FUEL,
            name="SAP fuel export",
        )
        self.batch = IngestionBatch.objects.create(
            data_source=self.data_source,
            uploaded_by="parser-test",
            raw_file=ContentFile(b"", name="sap.csv"),
        )

    def parse_single_row(self, row):
        return parse_sap_fuel_csv(StringIO(CSV_HEADER + row), self.batch)[0]

    def test_normal_row_maps_sap_fields_and_normalizes_liters(self):
        record = self.parse_single_row(
            "4900001001;03.01.2026;1000;DIESEL-001;Diesel EN590;1.234,56;L;FLEET-100\n"
        )

        self.assertTrue(record._state.adding)
        self.assertEqual(record.client, self.client_obj)
        self.assertEqual(record.data_source, self.data_source)
        self.assertEqual(record.batch, self.batch)
        self.assertEqual(record.scope, EmissionRecord.Scope.SCOPE_1)
        self.assertEqual(record.activity_date.isoformat(), "2026-01-03")
        self.assertEqual(record.period_start, record.activity_date)
        self.assertEqual(record.period_end, record.activity_date)
        self.assertEqual(record.activity_type, "diesel_combustion")
        self.assertEqual(record.raw_value, Decimal("1234.56"))
        self.assertEqual(record.raw_unit, "L")
        self.assertEqual(record.source_row_id, "4900001001")
        self.assertEqual(record.status, EmissionRecord.Status.PENDING_REVIEW)
        self.assertEqual(record.flag_reason, "")
        self.assertEqual(record.raw_payload["original_row"]["Buchungsdatum"], "03.01.2026")
        self.assertEqual(record.raw_payload["facility_name"], "Berlin Manufacturing Plant")

    def test_zero_quantity_is_flagged(self):
        record = self.parse_single_row(
            "4900001019;26.02.2026;3000;DIESEL-001;Diesel Testlauf;0,00;L;GEN-350\n"
        )

        self.assertEqual(record.status, EmissionRecord.Status.FLAGGED)
        self.assertIn("Quantity is zero", record.flag_reason)
        self.assertEqual(record.raw_value, Decimal("0.00"))

    def test_unknown_unit_is_flagged(self):
        record = self.parse_single_row(
            "4900002001;04.03.2026;2000;NATGAS-002;Erdgas Test;99,50;KWH;PROC-220\n"
        )

        self.assertEqual(record.status, EmissionRecord.Status.FLAGGED)
        self.assertIn("Unrecognized unit for natural gas: KWH", record.flag_reason)
        self.assertEqual(record.raw_value, Decimal("99.50"))
        self.assertEqual(record.raw_unit, "KWH")

    def test_german_decimal_parsing_and_gallon_conversion(self):
        record = self.parse_single_row(
            "4900001004;10.01.2026;3000;DIESEL-001;Diesel Generator;850,40;GAL;GEN-300\n"
        )

        self.assertEqual(record.status, EmissionRecord.Status.PENDING_REVIEW)
        self.assertEqual(record.raw_unit, "L")
        self.assertEqual(record.raw_value, Decimal("850.40") * Decimal("3.785411784"))
        self.assertEqual(record.raw_payload["source_quantity"], "850.40")
