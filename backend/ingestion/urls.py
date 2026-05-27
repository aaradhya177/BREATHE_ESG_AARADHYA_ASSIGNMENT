from django.urls import path

from ingestion import views


urlpatterns = [
    path("ingest/sap/", views.SapIngestView.as_view(), name="ingest-sap"),
    path("ingest/utility/", views.UtilityIngestView.as_view(), name="ingest-utility"),
    path("ingest/travel/", views.TravelIngestView.as_view(), name="ingest-travel"),
    path("batches/", views.BatchListView.as_view(), name="batch-list"),
    path("records/", views.RecordListView.as_view(), name="record-list"),
    path("records/<uuid:record_id>/", views.RecordDetailView.as_view(), name="record-detail"),
    path("records/<uuid:record_id>/review/", views.RecordReviewView.as_view(), name="record-review"),
    path("records/<uuid:record_id>/audit-log/", views.RecordAuditLogView.as_view(), name="record-audit-log"),
]
