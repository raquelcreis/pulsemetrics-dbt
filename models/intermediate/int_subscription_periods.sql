
-- One row per subscription and completed calendar month
-- when the subscription is active at month end.
--
-- Lifecycle interval: [start_date, end_date)
-- Start is inclusive; end is exclusive.

WITH subscriptions AS (

    SELECT
        subscription_id,
        customer_id,
        plan_id,
        start_date,
        end_date,
        created_at
    FROM {{ ref('stg_subscriptions') }}

),

month_bounds AS (

    SELECT
        DATE_TRUNC('MONTH', MIN(start_date))::DATE AS first_month,
        DATEADD(
            MONTH,
            -1,
            DATE_TRUNC('MONTH', CURRENT_DATE())
        )::DATE AS last_month
    FROM subscriptions

),

month_sequence AS (

    SELECT
        SEQ4() AS month_number
    FROM TABLE(GENERATOR(ROWCOUNT => 100))

),

billing_months AS (

    SELECT
        DATEADD(
            MONTH,
            seq.month_number,
            bounds.first_month
        )::DATE AS month_start
    FROM month_bounds AS bounds
    CROSS JOIN month_sequence AS seq
    WHERE DATEADD(
        MONTH,
        seq.month_number,
        bounds.first_month
    ) <= bounds.last_month

),

subscription_months AS (

    SELECT
        s.subscription_id,
        s.customer_id,
        s.plan_id,
        m.month_start,
        s.start_date,
        s.end_date,
        s.created_at
    FROM subscriptions AS s
    INNER JOIN billing_months AS m
        ON s.start_date < DATEADD(
            MONTH,
            1,
            m.month_start
        )
        AND (
            s.end_date IS NULL
            OR s.end_date >= DATEADD(MONTH, 1, m.month_start)
        )

)

SELECT
    subscription_id,
    customer_id,
    plan_id,
    month_start,
    start_date,
    end_date,
    created_at,
    TRUE AS is_active
FROM subscription_months
