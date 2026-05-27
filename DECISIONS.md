# Design Decisions

## SAP Flat File Instead of IDoc/OData

I chose SAP flat-file ingestion because it is the lowest-friction path for a prototype. Many ESG teams can get BAPI/report extracts from SAP long before they can get an approved integration user, OData service exposure, middleware routing, or IDoc partner profile work.

The current implementation handles SAP fuel rows only. It does not handle procurement purchase orders, goods receipts, vendor material master enrichment, cost allocation, or cross-company-code reconciliation.

This means the parser accepts operational messiness that real SAP exports contain: German headers, semicolon delimiters, German decimal formats, material codes, plant codes, and mixed fuel units.

## Utility Portal CSV Instead of PDF Parsing

I chose portal CSV exports because they preserve structured fields: account number, meter, billing dates, kWh, demand, tariff, and cost. PDF utility bills are display documents, not data contracts. They vary by utility, redesign, page layout, OCR quality, and account type.

The current implementation handles electricity summary rows only. It does not parse PDFs, interval reads, reactive power, taxes, estimated/actual read flags, tariff line items, net metering export, or multi-currency billing.

## Concur/Navan JSON Upload Instead of OAuth API

I chose JSON file upload for travel because OAuth/API integration is usually a procurement/security project of its own. A JSON export lets the prototype validate the data model, review workflow, missing-distance handling, and emission factor calculations without waiting on vendor tenant configuration.

The current implementation handles travel expense records for air, hotel, car, and rail. It does not handle approvals, expense report hierarchy, attendees, corporate card matching, refunds, multi-leg itineraries, currency conversion, or automatic airport-distance lookup.

## Source Coverage

- SAP: fuel combustion only (`DIESEL-001`, `NATGAS-002`, `HFO-003`). No SAP procurement PO ingestion yet.
- Utility: purchased electricity billing rows only. No PDF extraction and no interval-meter file format.
- Travel: uploaded JSON expense rows. No OAuth sync, no itinerary service, no employee org mapping.

## Questions for the PM

1. Which emissions workflows must be auditable for the demo: ingestion only, review actions, calculation changes, or all three?
2. Are we reporting by operational facility, legal entity, cost center, or client-level aggregate first?
3. For SAP, is the first production source fuel movements, purchase orders, invoices, or material documents?
4. For travel, should missing flight distance block approval, or should analysts be allowed to approve with a manual estimate?
5. Which emission factor set is contractually expected for the customer: DEFRA, EPA, IEA, eGRID, country-specific grid factors, or a customer-provided library?
