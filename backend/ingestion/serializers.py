from rest_framework import serializers

from emissions.models import AuditLog, EmissionRecord, IngestionBatch


class IngestionBatchSerializer(serializers.ModelSerializer):
    source_type = serializers.CharField(source="data_source.source_type")

    class Meta:
        model = IngestionBatch
        fields = [
            "id",
            "source_type",
            "uploaded_at",
            "status",
            "row_count",
            "error_count",
        ]


class EmissionRecordSerializer(serializers.ModelSerializer):
    client_id = serializers.IntegerField(source="client.id", read_only=True)
    data_source_id = serializers.IntegerField(source="data_source.id", read_only=True)
    source_type = serializers.CharField(source="data_source.source_type", read_only=True)
    batch_id = serializers.IntegerField(source="batch.id", read_only=True)

    class Meta:
        model = EmissionRecord
        fields = [
            "id",
            "client_id",
            "data_source_id",
            "source_type",
            "batch_id",
            "scope",
            "activity_date",
            "period_start",
            "period_end",
            "activity_type",
            "raw_value",
            "raw_unit",
            "normalized_value_kwh",
            "co2e_kg",
            "emission_factor_used",
            "source_row_id",
            "raw_payload",
            "status",
            "flag_reason",
            "reviewed_by",
            "reviewed_at",
            "is_edited",
            "edit_notes",
            "created_at",
            "updated_at",
        ]


class AuditLogSerializer(serializers.ModelSerializer):
    emission_record_id = serializers.UUIDField(source="emission_record.id", read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "emission_record_id",
            "action",
            "actor",
            "timestamp",
            "before_state",
            "after_state",
        ]
