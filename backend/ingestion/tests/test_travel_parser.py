from decimal import Decimal
from io import StringIO

from django.core.files.base import ContentFile
from django.test import TestCase

from emissions.models import Client, DataSource, EmissionRecord, IngestionBatch
from ingestion.parsers.travel_parser import parse_travel_json
from ingestion.utils.emission_factors import DEFRA_2023_TRAVEL_FACTORS


class TravelParserTests(TestCase):
    def setUp(self):
        self.client_obj = Client.objects.create(name="Acme Corp", slug="acme-corp")
        self.data_source = DataSource.objects.create(
            client=self.client_obj,
            source_type=DataSource.SourceType.TRAVEL_FLIGHT,
            name="Travel expense export",
        )
        self.batch = IngestionBatch.objects.create(
            data_source=self.data_source,
            uploaded_by="parser-test",
            raw_file=ContentFile(b"", name="travel.json"),
        )

    def parse_single_record(self, record_json):
        return parse_travel_json(StringIO(f"[{record_json}]"), self.batch)[0]

    def test_flight_class_maps_activity_and_computes_co2e(self):
        record = self.parse_single_record(
            """
            {
              "expense_id": "EXP-0004",
              "employee_id": "E1004",
              "trip_date": "2026-01-17",
              "category": "Air",
              "vendor": "Delta",
              "origin": "SFO",
              "destination": "JFK",
              "distance_km": 4160,
              "cost_usd": 1850.0,
              "nights": null,
              "flight_class": "Business"
            }
            """
        )

        expected = Decimal("4160") * DEFRA_2023_TRAVEL_FACTORS["flight_business"]["factor"]
        self.assertTrue(record._state.adding)
        self.assertEqual(record.scope, EmissionRecord.Scope.SCOPE_3)
        self.assertEqual(record.activity_type, "flight_business")
        self.assertEqual(record.raw_value, Decimal("4160"))
        self.assertEqual(record.raw_unit, "km")
        self.assertEqual(record.co2e_kg, expected)
        self.assertEqual(record.status, EmissionRecord.Status.PENDING_REVIEW)
        self.assertEqual(record.raw_payload["origin"], "SFO")

    def test_missing_flight_distance_is_flagged_but_record_is_created(self):
        record = self.parse_single_record(
            """
            {
              "expense_id": "EXP-0013",
              "employee_id": "E1012",
              "trip_date": "2026-03-01",
              "category": "Air",
              "vendor": "United",
              "origin": "ORD",
              "destination": "LAX",
              "distance_km": null,
              "cost_usd": 620.25,
              "nights": null,
              "flight_class": "Economy"
            }
            """
        )

        self.assertEqual(record.activity_type, "flight_economy")
        self.assertEqual(record.status, EmissionRecord.Status.FLAGGED)
        self.assertEqual(record.flag_reason, "missing_distance_estimate_required")
        self.assertEqual(record.co2e_kg, None)
        self.assertEqual(record.raw_value, Decimal("0"))

    def test_hotel_nights_compute_co2e(self):
        record = self.parse_single_record(
            """
            {
              "expense_id": "EXP-0002",
              "employee_id": "E1002",
              "trip_date": "2026-01-11",
              "category": "Hotel",
              "vendor": "Taj MG Road",
              "origin": "Bengaluru",
              "destination": "Bengaluru",
              "distance_km": null,
              "cost_usd": 420.0,
              "nights": 3,
              "flight_class": null
            }
            """
        )

        self.assertEqual(record.activity_type, "hotel_stay")
        self.assertEqual(record.raw_value, Decimal("3"))
        self.assertEqual(record.raw_unit, "nights")
        self.assertEqual(record.co2e_kg, Decimal("45.0"))
