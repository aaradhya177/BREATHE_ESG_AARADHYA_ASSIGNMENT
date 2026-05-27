from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

from emissions.models import Client, EmissionRecord


SAP_CSV = (
    "Belegnummer;Buchungsdatum;Werk;Materialnummer;Materialkurztext;Menge;Mengeneinheit;Kostenstelle\n"
    "4900001001;03.01.2026;1000;DIESEL-001;Diesel EN590;1.234,56;L;FLEET-100\n"
    "4900001019;26.02.2026;3000;DIESEL-001;Diesel Testlauf;0,00;L;GEN-350\n"
)

UTILITY_CSV = (
    "account_number,meter_id,site_name,billing_period_start,billing_period_end,"
    "consumption_kwh,demand_kw,tariff_code,cost_local_currency\n"
    "ACC-2001,MTR-MYS-001,Mysuru Components,2026-02-18,2026-03-17,"
    "13.42 MWh,211.7,HT2B,128540.20\n"
)

TRAVEL_JSON = b"""
[
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
]
"""


class IngestionApiTests(TestCase):
    def setUp(self):
        self.client_obj = Client.objects.create(name="Acme Corp", slug="acme-corp")
        self.api = APIClient()

    def upload(self, url, content, filename):
        return self.api.post(
            url,
            {
                "file": SimpleUploadedFile(filename, content),
                "client_slug": "acme-corp",
                "uploaded_by": "api-test",
            },
            format="multipart",
        )

    def test_sap_ingest_creates_batch_and_records(self):
        response = self.upload("/api/ingest/sap/", SAP_CSV.encode(), "sap.csv")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], "COMPLETED")
        self.assertEqual(response.data["row_count"], 2)
        self.assertEqual(response.data["error_count"], 0)
        self.assertEqual(response.data["flagged_count"], 1)
        self.assertEqual(EmissionRecord.objects.count(), 2)

    def test_utility_and_travel_ingest_endpoints(self):
        utility_response = self.upload("/api/ingest/utility/", UTILITY_CSV.encode(), "utility.csv")
        travel_response = self.upload("/api/ingest/travel/", TRAVEL_JSON, "travel.json")

        self.assertEqual(utility_response.status_code, 201)
        self.assertEqual(utility_response.data["row_count"], 1)
        self.assertEqual(travel_response.status_code, 201)
        self.assertEqual(travel_response.data["row_count"], 1)
        self.assertEqual(travel_response.data["flagged_count"], 1)

    def test_batch_list_record_list_review_and_audit_log(self):
        ingest_response = self.upload("/api/ingest/sap/", SAP_CSV.encode(), "sap.csv")
        batch_id = ingest_response.data["batch_id"]

        batches_response = self.api.get("/api/batches/", {"client_slug": "acme-corp"})
        self.assertEqual(batches_response.status_code, 200)
        self.assertEqual(batches_response.data[0]["id"], batch_id)
        self.assertEqual(batches_response.data[0]["source_type"], "SAP_FUEL")

        records_response = self.api.get(
            "/api/records/",
            {"batch_id": batch_id, "status": "PENDING_REVIEW"},
        )
        self.assertEqual(records_response.status_code, 200)
        self.assertEqual(records_response.data["count"], 1)
        record_id = records_response.data["results"][0]["id"]
        self.assertIn("flag_reason", records_response.data["results"][0])

        review_response = self.api.patch(
            f"/api/records/{record_id}/review/",
            {
                "action": "APPROVE",
                "reviewer": "Ada",
                "edit_notes": "Reviewed against source file.",
            },
            format="json",
        )
        self.assertEqual(review_response.status_code, 200)
        self.assertEqual(review_response.data["status"], "APPROVED")
        self.assertEqual(review_response.data["reviewed_by"], "Ada")
        self.assertTrue(review_response.data["is_edited"])

        audit_response = self.api.get(f"/api/records/{record_id}/audit-log/")
        self.assertEqual(audit_response.status_code, 200)
        self.assertEqual(len(audit_response.data), 1)
        self.assertEqual(audit_response.data[0]["action"], "APPROVE")
        self.assertEqual(audit_response.data[0]["actor"], "Ada")

    def test_missing_file_returns_400(self):
        response = self.api.post(
            "/api/ingest/sap/",
            {"client_slug": "acme-corp", "uploaded_by": "api-test"},
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
