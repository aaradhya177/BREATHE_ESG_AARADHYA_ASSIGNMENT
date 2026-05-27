# Data Model

This project models emissions ingestion as a tenant-owned audit trail. The core idea is simple: keep the raw source row, normalize the operational fields needed for review/reporting, and never lose the link back to the upload that produced the record.

## Client

`Client` is the multi-tenancy root. It uses the default integer `BigAutoField` primary key because clients are internal records managed by this database. They do not need to be portable across exports or external systems.

Fields:

- `id`: local database identity.
- `name`: display name, e.g. `Acme Corp`.
- `slug`: unique stable key used by API clients (`client_slug=acme-corp`). The slug avoids exposing numeric IDs and remains easier to pass in forms and URLs.
- `created_at`: operational timestamp for tenant creation.

## DataSource

`DataSource` describes the origin of a file or integration stream for one client.

Fields:

- `client`: foreign key to `Client`. Every source belongs to one tenant.
- `source_type`: constrained choices so ingestion code can branch by known source family: SAP fuel, SAP procurement, utility electricity, travel flight, travel hotel, and travel ground.
- `name`: human-readable source label.
- `description`: optional operator context.
- `created_at`: source registration timestamp.

## IngestionBatch

`IngestionBatch` is one uploaded file/import run.

Fields:

- `data_source`: links the batch to the source family and client.
- `uploaded_at`: when the file entered the system.
- `uploaded_by`: text field instead of an auth FK because the prototype intentionally has no user model yet.
- `status`: `PENDING`, `PROCESSING`, `COMPLETED`, or `FAILED`.
- `raw_file`: original uploaded file for replay/debugging.
- `row_count`: number of parsed records.
- `error_count`: number of hard parse/import errors. Row-level review issues are represented as flagged records, not errors.
- `notes`: failure notes or operator context.

## EmissionRecord

`EmissionRecord` is the normalized row-level fact table.

It uses a UUID primary key because emission records are likely to be referenced outside the database: CSV exports, audit packets, reviewer links, and future integrations. UUIDs avoid leaking sequence counts and remain stable if data moves between environments. `Client`, `DataSource`, and `IngestionBatch` keep integer IDs because they are local relational infrastructure.

Fields:

- `client`: direct tenant FK. This duplicates the tenant reachable through `data_source` and `batch`, intentionally. It keeps tenant filtering simple and safer in every records query.
- `data_source`: source that produced the row.
- `batch`: upload/import run that produced the row.
- `scope`: GHG Protocol scope.
- `activity_date`: primary date for the activity.
- `period_start`, `period_end`: billing/reporting interval support, especially for utilities.
- `activity_type`: calculation category such as `diesel_combustion`, `grid_electricity`, or `flight_business`.
- `raw_value`, `raw_unit`: normalized activity quantity in a parser-specific base unit.
- `normalized_value_kwh`: comparable energy quantity where applicable. Electricity writes kWh directly; fuel parsers currently normalize physical units first and leave kWh conversion for the calculation layer.
- `co2e_kg`: final emissions output in kilograms CO2e.
- `emission_factor_used`: factor name/version used for the calculation.
- `source_row_id`: original row identifier or a deterministic fallback.
- `raw_payload`: full original source row/record plus parser metadata. This is the source-of-truth preservation field. It lets analysts debug transformations without reopening the uploaded file.
- `status`: `PENDING_REVIEW`, `FLAGGED`, `APPROVED`, or `REJECTED`.
- `flag_reason`: row-level quality issue, e.g. missing flight distance.
- `reviewed_by`, `reviewed_at`: lightweight reviewer tracking until real auth exists.
- `is_edited`, `edit_notes`: marks post-ingestion human changes and stores reviewer explanation.
- `created_at`, `updated_at`: lifecycle timestamps.

## AuditLog

`AuditLog` stores review/change history for each `EmissionRecord`.

Fields:

- `emission_record`: record being changed.
- `action`: workflow action, e.g. `APPROVE`, `REJECT`, or `FLAG`.
- `actor`: text reviewer/system actor.
- `timestamp`: when the action happened.
- `before_state`, `after_state`: JSON snapshots from the serializer before and after the update.

The audit model and `EmissionRecord.is_edited` serve different purposes. `AuditLog` is the event history. `is_edited` is a quick query/display flag that says the record has been changed after ingestion.

## Scope Assignment

- SAP fuel parser: Scope 1. These are direct fuel combustion activities.
- Utility electricity parser: Scope 2. Purchased electricity is indirect energy consumption.
- Travel parser: Scope 3. Air, hotel, car, and rail expenses are value-chain/business-travel emissions.

## Unit Strategy

The project separates three concepts:

- Source units: preserved in `raw_payload`.
- Parser base units: written to `raw_value` and `raw_unit` (`L` for liquid fuel, `M3` for gas, `kWh` for electricity, `km` or `nights` for travel).
- Reporting/calculation outputs: `normalized_value_kwh` for energy comparability where meaningful, and `co2e_kg` as the emissions output.

This keeps ingestion honest. The parser should not pretend every source can be converted to kWh without fuel properties or region-specific assumptions. The calculation layer can fill `normalized_value_kwh` and `co2e_kg` as factors mature.
