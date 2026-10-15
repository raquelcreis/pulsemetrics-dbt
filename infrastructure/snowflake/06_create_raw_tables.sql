USE ROLE PULSEMETRICS_DBT;
USE DATABASE PULSEMETRICS;

CREATE SCHEMA IF NOT EXISTS RAW;


-- ============================================================
-- RAW.CUSTOMERS
-- Grain: 1 row = 1 customer/company
-- ============================================================

CREATE OR REPLACE TABLE RAW.CUSTOMERS (
    id              VARCHAR NOT NULL,
    customer_name   VARCHAR,
    document        VARCHAR NOT NULL,
    email           VARCHAR NOT NULL,
    country         VARCHAR NOT NULL,
    created_at      TIMESTAMP_NTZ NOT NULL
);


-- ============================================================
-- RAW.PLANS
-- Grain: 1 row = 1 immutable commercial plan version
-- ============================================================

CREATE OR REPLACE TABLE RAW.PLANS (
    plan_id         VARCHAR NOT NULL,
    plan_name       VARCHAR NOT NULL,
    monthly_price   NUMBER(18,2) NOT NULL,
    billing_cycle   VARCHAR NOT NULL
);


-- ============================================================
-- RAW.SUBSCRIPTIONS
-- Grain: 1 row = 1 customer subscription period/version
-- ============================================================

CREATE OR REPLACE TABLE RAW.SUBSCRIPTIONS (
    subscription_id VARCHAR NOT NULL,
    customer_id     VARCHAR NOT NULL,
    plan_id         VARCHAR NOT NULL,
    start_date      DATE NOT NULL,
    end_date        DATE,
    created_at      TIMESTAMP_NTZ NOT NULL
);


-- ============================================================
-- RAW.PAYMENTS
-- Grain: 1 row = 1 payment attempt for 1 billing period
-- ============================================================

CREATE OR REPLACE TABLE RAW.PAYMENTS (
    payment_id                VARCHAR NOT NULL,
    subscription_id           VARCHAR NOT NULL,
    billing_period_start_date DATE NOT NULL,
    payment_datetime          TIMESTAMP_NTZ NOT NULL,
    amount                    NUMBER(18,2) NOT NULL,
    currency                  VARCHAR NOT NULL,
    status                    VARCHAR NOT NULL,
    payment_method            VARCHAR NOT NULL,
    created_at                TIMESTAMP_NTZ NOT NULL
);


-- ============================================================
-- RAW.PRODUCT_EVENTS
-- Grain: 1 row = 1 customer/account product action
-- ============================================================

CREATE OR REPLACE TABLE RAW.PRODUCT_EVENTS (
    event_id         VARCHAR NOT NULL,
    customer_id      VARCHAR NOT NULL,
    event_type       VARCHAR NOT NULL,
    event_timestamp  TIMESTAMP_NTZ NOT NULL,
    event_properties VARIANT,
    created_at       TIMESTAMP_NTZ NOT NULL
);