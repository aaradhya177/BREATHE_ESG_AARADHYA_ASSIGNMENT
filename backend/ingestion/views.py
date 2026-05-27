from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from emissions.models import AuditLog, Client, DataSource, EmissionRecord, IngestionBatch
from ingestion.parsers.sap_parser import SapFuelParserError, parse_sap_fuel_csv
from ingestion.parsers.travel_parser import TravelParserError, parse_travel_json
from ingestion.parsers.utility_parser import UtilityParserError, parse_utility_csv
from ingestion.serializers import AuditLogSerializer, EmissionRecordSerializer, IngestionBatchSerializer


class StandardResultsPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200


class BaseIngestView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    source_type = None
    source_name = None
    parser_function = None
    parser_errors = (ValueError, UnicodeDecodeError, KeyError, TypeError)

    def post(self, request):
        uploaded_file = request.FILES.get("file")
        client_slug = request.data.get("client_slug")
        uploaded_by = request.data.get("uploaded_by")

        if uploaded_file is None:
            return Response({"detail": "file is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not client_slug:
            return Response({"detail": "client_slug is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not uploaded_by:
            return Response({"detail": "uploaded_by is required"}, status=status.HTTP_400_BAD_REQUEST)

        client = get_object_or_404(Client, slug=client_slug)
        data_source, _created = DataSource.objects.get_or_create(
            client=client,
            source_type=self.source_type,
            name=self.source_name,
        )
        batch = IngestionBatch.objects.create(
            data_source=data_source,
            uploaded_by=uploaded_by,
            status=IngestionBatch.Status.PROCESSING,
            raw_file=uploaded_file,
        )

        try:
            with batch.raw_file.open("rb") as stored_file:
                records = self.parser_function(stored_file, batch)
        except self.parser_errors as exc:
            batch.status = IngestionBatch.Status.FAILED
            batch.row_count = 0
            batch.error_count = 1
            batch.notes = str(exc)
            batch.save(update_fields=["status", "row_count", "error_count", "notes"])
            return Response(
                {
                    "batch_id": batch.id,
                    "status": batch.status,
                    "row_count": batch.row_count,
                    "error_count": batch.error_count,
                    "flagged_count": 0,
                    "detail": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        flagged_count = sum(1 for record in records if record.status == EmissionRecord.Status.FLAGGED)
        with transaction.atomic():
            EmissionRecord.objects.bulk_create(records)
            batch.status = IngestionBatch.Status.COMPLETED
            batch.row_count = len(records)
            batch.error_count = 0
            batch.save(update_fields=["status", "row_count", "error_count"])

        return Response(
            {
                "batch_id": batch.id,
                "status": batch.status,
                "row_count": batch.row_count,
                "error_count": batch.error_count,
                "flagged_count": flagged_count,
            },
            status=status.HTTP_201_CREATED,
        )


class SapIngestView(BaseIngestView):
    source_type = DataSource.SourceType.SAP_FUEL
    source_name = "SAP fuel upload"
    parser_function = staticmethod(parse_sap_fuel_csv)
    parser_errors = (SapFuelParserError, UnicodeDecodeError, KeyError, TypeError)


class UtilityIngestView(BaseIngestView):
    source_type = DataSource.SourceType.UTILITY_ELECTRICITY
    source_name = "Utility electricity upload"
    parser_function = staticmethod(parse_utility_csv)
    parser_errors = (UtilityParserError, UnicodeDecodeError, KeyError, TypeError)


class TravelIngestView(BaseIngestView):
    source_type = DataSource.SourceType.TRAVEL_FLIGHT
    source_name = "Travel expense upload"
    parser_function = staticmethod(parse_travel_json)
    parser_errors = (TravelParserError, UnicodeDecodeError, KeyError, TypeError)


class BatchListView(APIView):
    def get(self, request):
        client_slug = request.query_params.get("client_slug")
        if not client_slug:
            return Response({"detail": "client_slug is required"}, status=status.HTTP_400_BAD_REQUEST)

        client = get_object_or_404(Client, slug=client_slug)
        batches = (
            IngestionBatch.objects.filter(data_source__client=client)
            .select_related("data_source")
            .order_by("-uploaded_at")
        )
        return Response(IngestionBatchSerializer(batches, many=True).data)


class RecordListView(APIView):
    pagination_class = StandardResultsPagination

    def get(self, request):
        batch_id = request.query_params.get("batch_id")
        if not batch_id:
            return Response({"detail": "batch_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        get_object_or_404(IngestionBatch, id=batch_id)
        records = EmissionRecord.objects.filter(batch_id=batch_id).order_by("-activity_date", "-created_at")
        for field in ("status", "scope", "activity_type"):
            value = request.query_params.get(field)
            if value:
                records = records.filter(**{field: value})

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(records, request)
        serializer = EmissionRecordSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class RecordDetailView(APIView):
    def get(self, request, record_id):
        record = get_object_or_404(EmissionRecord, id=record_id)
        return Response(EmissionRecordSerializer(record).data)


class RecordReviewView(APIView):
    ACTION_TO_STATUS = {
        "APPROVE": EmissionRecord.Status.APPROVED,
        "REJECT": EmissionRecord.Status.REJECTED,
        "FLAG": EmissionRecord.Status.FLAGGED,
    }

    def patch(self, request, record_id):
        record = get_object_or_404(EmissionRecord, id=record_id)
        action = request.data.get("action")
        reviewer = request.data.get("reviewer")

        if action not in self.ACTION_TO_STATUS:
            return Response(
                {"detail": 'action must be one of "APPROVE", "REJECT", or "FLAG"'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not reviewer:
            return Response({"detail": "reviewer is required"}, status=status.HTTP_400_BAD_REQUEST)

        before_state = dict(EmissionRecordSerializer(record).data)
        record.status = self.ACTION_TO_STATUS[action]
        record.reviewed_by = reviewer
        record.reviewed_at = timezone.now()
        if "flag_reason" in request.data:
            record.flag_reason = request.data.get("flag_reason") or ""
        if "edit_notes" in request.data:
            record.edit_notes = request.data.get("edit_notes") or ""
            record.is_edited = bool(record.edit_notes)
        record.save()
        after_state = dict(EmissionRecordSerializer(record).data)

        AuditLog.objects.create(
            emission_record=record,
            action=action,
            actor=reviewer,
            before_state=before_state,
            after_state=after_state,
        )

        return Response(after_state)


class RecordAuditLogView(APIView):
    def get(self, request, record_id):
        record = get_object_or_404(EmissionRecord, id=record_id)
        logs = record.audit_logs.all().order_by("-timestamp")
        return Response(AuditLogSerializer(logs, many=True).data)
