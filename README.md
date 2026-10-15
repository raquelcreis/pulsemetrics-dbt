# PulseMetrics — SaaS Analytics Engineering

PulseMetrics is a portfolio project focused on building an analytics engineering workflow for a fictional B2B SaaS business.

The project uses synthetic data to model customers, subscriptions, payments, and product events. It explores how raw operational data can be transformed into reliable, documented analytical models using dbt and Snowflake.

## Tech Stack

- **Data warehouse:** Snowflake
- **Transformation:** dbt Core
- **Data generation and ingestion:** Python, pandas, Snowflake Connector
- **Testing and documentation:** dbt tests and SQL-based data quality checks

## Architecture

The project follows a layered data modeling approach:

- **RAW:** source tables loaded into Snowflake.
- **STAGING:** standardized and tested source models.
- **INTERMEDIATE:** business logic and reusable transformations.
- **MARTS:** business-facing analytical models.

## Current Progress

- [x] Synthetic data generation for customers, subscriptions, payments, and product events.
- [x] Snowflake database, schemas, roles, and ingestion setup.
- [x] Python ingestion pipeline for RAW tables.
- [x] dbt staging models and data quality tests.
- [x] Billing period consolidation to handle multiple payment attempts.
- [x] Subscription lifecycle modeling at monthly grain.
- [x] Customer-level contracted MRR modeling.
- [x] Monthly revenue mart with active customers, active subscriptions, contracted MRR, and ARPA.
- [x] Initial data quality tests and documentation for the revenue mart.
- [x] Initial documentation of the customer churn proxy methodology.
- [ ] Customer churn intermediate model and monthly churn mart.
- [ ] Additional business-facing marts and analytical insights.
- [ ] Automated validation in CI.

## Key Business Metrics

- **Contracted MRR:** monthly recurring revenue estimated from active subscriptions on monthly plans.
- **ARPA (Average Revenue Per Account):** contracted MRR divided by the number of active customers.
- **Customer churn:** planned as a proxy derived from subscription lifecycle dates, identifying when a customer has no active subscriptions remaining.

## Data and Methodology Notes

The data is synthetic and intended for learning and demonstration.

Customer churn is not directly recorded as an explicit cancellation event in the source data. The planned methodology reconstructs customer activity from subscription start and end dates. Assumptions and limitations are documented in `docs/metrics/customer_churn.md`.

## Repository Structure

```text
data_generation/   Synthetic data generation and ingestion
docs/              Metric definitions and methodology
infrastructure/    Snowflake setup and permissions SQL
macros/            Custom dbt macros
models/
  staging/         Source standardization and tests
  intermediate/    Reusable business logic
  marts/           Business-facing analytical models
seeds/             Static reference data
tests/             Singular SQL data quality tests
```

## Status

This project is actively being developed. Models, assumptions, tests, and documentation will evolve as new analytical requirements are implemented.