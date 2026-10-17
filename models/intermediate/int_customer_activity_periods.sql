
-- One row per continuous customer activity period.
-- Overlapping subscriptions and same-day transitions are merged.
--
-- Lifecycle interval: [start_date, end_date)
-- A NULL end_date represents an ongoing subscription.

WITH subscriptions AS (

    SELECT
        customer_id,
        subscription_id,
        start_date,
        end_date
    FROM {{ ref('stg_subscriptions') }}

),

ordered_subscriptions AS (

    SELECT
        customer_id,
        subscription_id,
        start_date,
        end_date,

        MAX(
            COALESCE(end_date, '9999-12-31'::DATE)
        ) OVER (
            PARTITION BY customer_id
            ORDER BY start_date, subscription_id
            ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
        ) AS previous_max_end_date

    FROM subscriptions

),

identified_periods AS (

    SELECT
        *,
        CASE
            WHEN previous_max_end_date IS NULL
                OR start_date > previous_max_end_date
            THEN 1
            ELSE 0
        END AS starts_new_period

    FROM ordered_subscriptions

),

numbered_periods AS (

    SELECT
        *,
        SUM(starts_new_period) OVER (
            PARTITION BY customer_id
            ORDER BY start_date, subscription_id
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS activity_period_number

    FROM identified_periods

),

customer_activity_periods AS (

    SELECT
        customer_id,
        activity_period_number,
        MIN(start_date) AS activity_start_date,

        CASE
            WHEN COUNT_IF(end_date IS NULL) > 0
                THEN NULL
            ELSE MAX(end_date)
        END AS activity_end_date,

        COUNT(DISTINCT subscription_id) AS subscriptions_in_period

    FROM numbered_periods
    GROUP BY
        customer_id,
        activity_period_number

)

SELECT
    customer_id,
    activity_period_number,
    activity_start_date,
    activity_end_date,
    subscriptions_in_period
FROM customer_activity_periods
