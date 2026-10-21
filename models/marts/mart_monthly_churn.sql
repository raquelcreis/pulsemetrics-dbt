
-- Monthly customer churn metrics.
-- Churn is inferred from subscription lifecycle dates.
--
-- Opening customer base: customers active immediately
-- before the start of each calendar month.
-- Only churn events from this opening base enter
-- the monthly churn-rate numerator.

WITH activity_periods AS (

    SELECT
        customer_id,
        activity_period_number,
        activity_start_date,
        activity_end_date
    FROM {{ ref('int_customer_activity_periods') }}

),

churn_events AS (

    SELECT
        customer_id,
        activity_period_number,
        churn_date
    FROM {{ ref('int_customer_churn_events') }}

),

months AS (

    SELECT month_start
    FROM {{ ref('int_calendar_months') }}

),

opening_customer_base AS (

    SELECT
        m.month_start,
        ap.customer_id,
        ap.activity_period_number
    FROM months AS m
    INNER JOIN activity_periods AS ap
        ON ap.activity_start_date < m.month_start
        AND (
            ap.activity_end_date IS NULL
            OR ap.activity_end_date >= m.month_start
        )

),

monthly_churn AS (

    SELECT
        b.month_start,
        COUNT(DISTINCT b.customer_id) AS churned_customers
    FROM opening_customer_base AS b
    INNER JOIN churn_events AS ce
        ON ce.customer_id = b.customer_id
        AND ce.activity_period_number = b.activity_period_number
        AND ce.churn_date >= b.month_start
        AND ce.churn_date < DATEADD(
            MONTH,
            1,
            b.month_start
        )
    GROUP BY b.month_start

),

opening_base_counts AS (

    SELECT
        month_start,
        COUNT(DISTINCT customer_id) AS opening_active_customers
    FROM opening_customer_base
    GROUP BY month_start

)

SELECT
    b.month_start,
    b.opening_active_customers,
    COALESCE(c.churned_customers, 0) AS churned_customers,

    COALESCE(c.churned_customers, 0)::FLOAT
        / NULLIF(b.opening_active_customers, 0)
        AS customer_churn_rate

FROM opening_base_counts AS b
LEFT JOIN monthly_churn AS c
    ON b.month_start = c.month_start
