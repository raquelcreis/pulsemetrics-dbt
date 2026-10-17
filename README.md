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
- [x] Subscription lifecycle modeling and completed-month revenue snapshots.
- [x] Customer-level contracted MRR modeling.
- [x] Monthly revenue mart with active customers, active subscriptions, contracted MRR, and ARPA.
- [x] Initial data quality tests and documentation for the revenue mart.
- [x] Initial documentation of the customer churn proxy methodology.
- [x] Customer churn proxy intermediate model and completed-month churn mart.
- [ ] Additional business-facing marts and analytical insights.
- [ ] Automated validation in CI.

## Key Business Metrics

- **Contracted MRR:** month-end run rate from active monthly subscriptions at the end of each completed month. It is not prorated or based on payment attempts.
- **Active customers and subscriptions:** customers with at least one active subscription, and subscriptions active, at the same month-end snapshot.
- **ARPA (Average Revenue Per Account):** month-end contracted MRR divided by month-end active customers.
- **Customer churn:** an estimate inferred when a customer's continuous subscription activity period ends. The monthly rate uses churned customers from the opening base divided by customers active immediately before the month began. Only completed months are included.

## Data and Methodology Notes

The data is synthetic and intended for learning and demonstration.

Customer churn is not directly recorded as an explicit cancellation event in the source data. The implemented proxy reconstructs customer activity from subscription start and end dates; same-day plan changes remain continuous, and reactivation is realized only when a later activity period has started. Assumptions and limitations are documented in `docs/metrics/customer_churn.md`.

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
