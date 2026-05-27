# Tradeoffs

## Cut 1: No Authentication or Multi-User Permissions

The prototype has no login, roles, or ownership checks. Reviewer names are plain strings.

Reasoning: the immediate goal is to prove ingestion, normalization, review, and audit flow. Adding auth now would slow iteration and create fake role decisions before the PM confirms real user types.

Production direction: use Django auth, DRF permissions, and JWT/session auth. Review actions should store a real user FK, and every query should enforce tenant access.

## Cut 2: No Real-Time Emission Factor API

Travel factors are hardcoded DEFRA 2023 approximate constants.

Reasoning: factor APIs introduce versioning, licensing, caching, retries, and explainability requirements. For the prototype, deterministic local factors make tests stable and keep the calculation path visible.

Production direction: build an emission-factor table with source, year, geography, unit, version, and effective date. External APIs can populate that table, but calculations should reference immutable local factor versions.

## Cut 3: No PDF Utility Bill Parsing

Utility ingestion accepts structured CSV only.

Reasoning: PDF parsing would consume a lot of engineering time for low reliability. Utility bills differ by provider, tariff, meter type, and layout. OCR/layout extraction errors are hard to detect and dangerous for emissions reporting.

Production direction: prefer utility portal CSV, Green Button XML/CSV, EDI, or direct utility data feeds. Add PDF parsing only as a fallback with human verification and confidence scoring.
