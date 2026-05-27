import uuid

from django.db import models


class Client(models.Model):
    """
    Root tenant for all ESG emissions data.

    Fields:
        id: Uses Django's configured BigAutoField primary key because this table is
            relational infrastructure and does not need globally portable IDs.
        name: Human-readable tenant name shown to operators and reports.
        slug: Unique stable identifier for URLs, imports, and integrations where
            display names may change or collide.
        created_at: Automatic timestamp for auditability of when the tenant was
            first created.
    """

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class DataSource(models.Model):
    """
    External system, file family, or import channel that produces activity data.

    Fields:
        id: Uses Django's BigAutoField primary key for simple local relational
            identity.
        client: ForeignKey to Client because every source belongs to exactly one
            tenant in the multi-tenant data model.
        source_type: Controlled TextChoices value so ingestion logic can branch
            consistently by known source category rather than free text.
        name: Human-friendly label for the concrete source, such as an SAP export
            name or a utility account.
        description: Optional longer context for operators; blank is allowed
            because many sources are self-explanatory at creation time.
        created_at: Automatic timestamp for tracking when this source was
            registered.
    """

    class SourceType(models.TextChoices):
        SAP_FUEL = "SAP_FUEL", "SAP fuel"
        SAP_PROCUREMENT = "SAP_PROCUREMENT", "SAP procurement"
        UTILITY_ELECTRICITY = "UTILITY_ELECTRICITY", "Utility electricity"
        TRAVEL_FLIGHT = "TRAVEL_FLIGHT", "Travel flight"
        TRAVEL_HOTEL = "TRAVEL_HOTEL", "Travel hotel"
        TRAVEL_GROUND = "TRAVEL_GROUND", "Travel ground"

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="data_sources")
    source_type = models.CharField(max_length=32, choices=SourceType.choices)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["client__name", "name"]

    def __str__(self):
        return f"{self.client}: {self.name}"


class IngestionBatch(models.Model):
    """
    One uploaded file or import run from a DataSource.

    Fields:
        id: Uses Django's BigAutoField primary key because batches are local
            workflow records and do not need UUID-level portability.
        data_source: ForeignKey to DataSource so every batch can be traced back
            to the source system and client context that produced it.
        uploaded_at: Automatic timestamp for the exact time the batch entered the
            platform.
        uploaded_by: CharField instead of an auth ForeignKey as requested, which
            keeps early ingestion independent from a final user model.
        status: Controlled TextChoices value for predictable batch workflow
            states from upload through processing completion or failure.
        raw_file: FileField storing the original uploaded artifact for replay,
            inspection, and audit.
        row_count: Integer counter for total parsed rows; defaults to zero so a
            pending batch can exist before parsing.
        error_count: Integer counter for failed rows; defaults to zero to make
            summary math straightforward.
        notes: Optional free-text operational notes or failure context.
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PROCESSING = "PROCESSING", "Processing"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name="batches")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.CharField(max_length=255)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    raw_file = models.FileField(upload_to="ingestion_batches/")
    row_count = models.PositiveIntegerField(default=0)
    error_count = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.data_source} batch {self.id}"


class EmissionRecord(models.Model):
    """
    Normalized activity row and computed emissions result.

    Fields:
        id: UUID primary key so emission records can be referenced safely across
            exports, audits, and future integrations without exposing sequence IDs.
        client: ForeignKey to Client for direct tenant filtering without needing
            to join through source or batch in every query.
        data_source: ForeignKey to DataSource preserving which configured source
            produced this row.
        batch: ForeignKey to IngestionBatch preserving the exact import run and
            uploaded file that created this row.
        scope: Controlled TextChoices value for GHG Protocol scope classification.
        activity_date: DateField for the primary date of the activity being
            measured, such as flight date, fuel purchase date, or meter date.
        period_start: DateField for interval-based activity data where the row
            covers a reporting period.
        period_end: DateField for the end of the interval, enabling monthly,
            quarterly, or custom period reporting.
        activity_type: CharField deliberately left as controlled application text
            rather than hard-coded choices because calculation categories will
            expand over time.
        raw_value: DecimalField to preserve numeric precision from source systems
            without floating point rounding errors.
        raw_unit: CharField storing the source unit so conversion decisions remain
            explainable and auditable.
        normalized_value_kwh: Nullable DecimalField because not every row may be
            normalized before review, but kWh equivalent enables cross-source
            comparability once available.
        co2e_kg: Nullable DecimalField because the emission calculation may happen
            after ingestion or be blocked by validation.
        emission_factor_used: CharField capturing the exact factor label/version
            applied to the row for reproducible calculations.
        source_row_id: CharField storing the original row identifier from the
            source file or system for traceability.
        raw_payload: JSONField storing the full original row so audit and debugging
            can inspect source values without re-opening the uploaded file.
        status: Controlled TextChoices review state for human validation workflow.
        flag_reason: Optional explanation for records needing attention.
        reviewed_by: Optional CharField instead of an auth ForeignKey so review
            tracking works before a final user model exists.
        reviewed_at: Nullable DateTimeField because records may not yet have been
            reviewed.
        is_edited: Boolean flag marking rows changed after ingestion.
        edit_notes: Optional explanation of post-ingestion edits.
        created_at: Automatic timestamp for insertion time.
        updated_at: Automatic timestamp for the most recent change.
    """

    class Scope(models.TextChoices):
        SCOPE_1 = "SCOPE_1", "Scope 1"
        SCOPE_2 = "SCOPE_2", "Scope 2"
        SCOPE_3 = "SCOPE_3", "Scope 3"

    class Status(models.TextChoices):
        PENDING_REVIEW = "PENDING_REVIEW", "Pending review"
        FLAGGED = "FLAGGED", "Flagged"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="emission_records")
    data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name="emission_records")
    batch = models.ForeignKey(IngestionBatch, on_delete=models.CASCADE, related_name="emission_records")
    scope = models.CharField(max_length=16, choices=Scope.choices)
    activity_date = models.DateField()
    period_start = models.DateField()
    period_end = models.DateField()
    activity_type = models.CharField(max_length=128)
    raw_value = models.DecimalField(max_digits=18, decimal_places=6)
    raw_unit = models.CharField(max_length=32)
    normalized_value_kwh = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    co2e_kg = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    emission_factor_used = models.CharField(max_length=255)
    source_row_id = models.CharField(max_length=255)
    raw_payload = models.JSONField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING_REVIEW)
    flag_reason = models.TextField(blank=True)
    reviewed_by = models.CharField(max_length=255, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    is_edited = models.BooleanField(default=False)
    edit_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-activity_date", "-created_at"]
        indexes = [
            models.Index(fields=["client", "scope"]),
            models.Index(fields=["client", "activity_date"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.client} {self.activity_type} {self.activity_date}"


class AuditLog(models.Model):
    """
    Immutable-style history entry for changes to an EmissionRecord.

    Fields:
        id: Uses Django's BigAutoField primary key for simple chronological audit
            row identity.
        emission_record: ForeignKey to EmissionRecord because each log entry
            describes one record-level action.
        action: CharField storing the action name, kept flexible so new workflow
            actions can be added without database migrations.
        actor: CharField instead of an auth ForeignKey so system processes,
            imports, and future users can all be represented.
        timestamp: Automatic timestamp for when the audited action occurred.
        before_state: JSONField snapshot of relevant values before the action,
            preserving a machine-readable audit trail.
        after_state: JSONField snapshot of relevant values after the action,
            enabling precise before/after comparison.
    """

    emission_record = models.ForeignKey(EmissionRecord, on_delete=models.CASCADE, related_name="audit_logs")
    action = models.CharField(max_length=128)
    actor = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    before_state = models.JSONField()
    after_state = models.JSONField()

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.action} on {self.emission_record_id} by {self.actor}"
