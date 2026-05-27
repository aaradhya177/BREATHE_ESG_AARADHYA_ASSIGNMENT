# Sources and Format Notes

This prototype was designed from common enterprise export patterns, not from a live customer system. The sample files are realistic enough for parser behavior, but they are not certified vendor schemas.

## SAP Fuel Flat Files

References:

- SAP Help Portal, file format options: https://help.sap.com/docs/PRODUCT_ID/018757bb7f5c4700a8840976c8730f34/ae74d5b5e01c4393bc2c2ade0b3826bd.html
- SAP Help Portal, file upload format: https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/8308e6d301d54584a33cd04a9861bc52/0b79741524714f8982819964874a35d7.html
- SAP KBA preview on semicolon CSV exports: https://userapps.support.sap.com/sap/support/knowledge/en/2784816

What I learned:

- SAP-adjacent file upload/export flows commonly support CSV and locale-sensitive parsing.
- Delimiters are configurable; semicolon-delimited files are common in European Excel/SAP workflows.
- Locale matters for dates and decimals. German-style formats are a real integration concern.

Why the sample looks this way:

- German headers (`Buchungsdatum`, `Menge`, `Mengeneinheit`) exercise header mapping.
- Semicolon delimiters avoid conflict with comma decimals.
- Quantities include `1.234,56` style formatting.
- Plant and material codes reflect how SAP exports often carry operational codes rather than friendly names.

What would break in production:

- Custom SAP reports may rename headers, include subtotal rows, use different encodings, or export quoted semicolons in descriptions.
- Material codes are customer-specific; the hardcoded mapping must become customer configuration.
- Unit conversion for fuel needs customer-approved densities/heating values, not parser constants.

## Utility Electricity CSV

References:

- Green Button Alliance utility bill data mapping: https://www.greenbuttonalliance.org/utility-bill-data
- Oracle utility self-service Green Button download notes: https://docs.oracle.com/en/industries/energy-water/digital-self-service/energy-management-overview/green-button-downloadmydata.html
- National Grid usage statement instructions mentioning spreadsheet/CSV and Green Button XML options: https://www.nationalgridus.com/media/pdfs/billing-payments/howtoretrieveutilityusagestatement.pdf

What I learned:

- Utility data is often available as structured exports, including CSV and Green Button formats.
- Meter/account identity, billing period, unit, and consumption are central fields.
- Billing periods do not necessarily align to calendar months, and usage can be reported per account, service point, or meter.

Why the sample looks this way:

- It has three meters across five billing periods to exercise multiple meters per site.
- Billing periods run from the 18th to the 17th to avoid false calendar-month assumptions.
- One row uses `MWh` to test unit normalization to kWh.

What would break in production:

- Some utilities export interval data rather than billing summaries.
- CSV schemas vary heavily by portal.
- Net metering, estimated reads, demand charges, taxes, and multiple service agreements need more fields.
- Negative consumption can be legitimate in export/net-metering contexts, but this prototype flags it.

## Corporate Travel JSON

References:

- SAP Concur developer/platform expense-entry style fields: https://api-explorer.bqecore.com/docs/api/apis/expenseentry
- CData SAP Concur expense entry field reference: https://cdn.cdata.com/help/FNJ/py/pg_table-reportdetailsexpenseentry.htm
- SAP Concur developer release note archive mentioning transaction date and vendor information: https://developer.concur.com/tools-support/release-notes/archive/app-center-dev-platform-2014-04-01.pdf

What I learned:

- Expense systems expose records around expense IDs, employees/resources, dates, vendors, categories, and amounts.
- Travel-specific emissions usually need data not always guaranteed by expense systems: distance, route, class of service, hotel nights, and transport mode.
- Flight records often carry airport codes; distance may require separate route enrichment.

Why the sample looks this way:

- It mixes Air, Hotel, Car, and Rail categories.
- Flight records include class because class changes emissions allocation.
- Some flights have IATA airport codes with missing distance to force review.
- Hotels use nights as the activity quantity.

What would break in production:

- Expense exports may not include distance or nights.
- Multi-leg flights need segment-level handling.
- Refunds, cancellations, split expenses, and currency conversion are not handled.
- Employee and department mapping would need HRIS integration.

## Render Deployment

References:

- Render Django deployment docs: https://render.com/docs/deploy-django
- Render deploy/start command docs: https://render.com/docs/deploys

What I learned:

- Render supports declarative `render.yaml` services.
- Django deployments commonly install dependencies, run `collectstatic`, run migrations, and start with `gunicorn`.
- Render PostgreSQL exposes a connection string suitable for `DATABASE_URL`.

What would break in production:

- Static file serving for Django admin/API browsable assets needs a production plan such as WhiteNoise or a separate static host.
- Secrets must be managed in Render environment groups, not committed.
- Database migrations should be reviewed for downtime before automated production deploys.
