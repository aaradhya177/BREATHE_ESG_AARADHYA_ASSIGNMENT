from decimal import Decimal
from io import StringIO

from django.core.files.base import ContentFile
from django.test import TestCase

from emissions.models import Client, DataSource, EmissionRecord, IngestionBatch
from ingestion.parsers.utility_parser import parse_utility_csv


CSV_HEADER = (
    "account_number,meter_id,site_name,billing_period_start,billing_period_end,"
    "consumption_kwh,demand_kw,tariff_code,cost_local_currency\n"
)


class UtilityParserTests(TestCase):
    def setUp(self):
        self.client_obj = Client.objects.create(name="Acme Corp", slug="acme-corp")
        self.data_source = DataSource.objects.create(
            client=self.client_obj,
            source_type=DataSource.SourceType.UTILITY_ELECTRICITY,
            name="Utility portal",
        )
        self.batch = IngestionBatch.objects.create(
            data_source=self.data_source,
            uploaded_by="parser-test",
            raw_file=ContentFile(b"", name="utility.csv"),
        )

    def parse_single_row(self, row):
        return parse_utility_csv(StringIO(CSV_HEADER + row), self.batch)[0]

    def test_normalizes_mwh_to_kwh(self):
        record = self.parse_single_row(
            "ACC-2001,MTR-MYS-001,Mysuru Components,2026-02-18,2026-03-17,"
            "13.42 MWh,211.7,HT2B,128540.20\n"
        )

        self.assertTrue(record._state.adding)
        self.assertEqual(record.scope, EmissionRecord.Scope.SCOPE_2)
        self.assertEqual(record.activity_type, "grid_electricity")
        self.assertEqual(record.raw_value, Decimal("13420.00"))
        self.assertEqual(record.raw_unit, "kWh")
        self.assertEqual(record.normalized_value_kwh, Decimal("13420.00"))
        self.assertEqual(record.raw_payload["meter_id"], "MTR-MYS-001")
        self.assertEqual(record.raw_payload["site_name"], "Mysuru Components")
        self.assertEqual(record.status, EmissionRecord.Status.PENDING_REVIEW)

    def test_flags_long_billing_period_and_negative_consumption(self):
        record = self.parse_single_row(
            "ACC-1001,MTR-BLR-001,Bengaluru Assembly,2026-01-01,2026-02-20,"
            "-25.5,312.4,HT2A,176890.25\n"
        )

        self.assertEqual(record.status, EmissionRecord.Status.FLAGGED)
        self.assertIn("billing_period_exceeds_45_days", record.flag_reason)
        self.assertIn("negative_consumption", record.flag_reason)
        self.assertEqual(record.raw_value, Decimal("-25.5"))
