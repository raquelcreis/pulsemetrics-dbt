
-- One row per observed customer activity-period end.
-- Churn is inferred from subscription lifecycle dates,
-- not from an explicit cancellation event.
--
-- Only activity periods that ended on or before today
-- are included. Future end dates are excluded.

WITH activity_periods AS (

    SELECT
        customer_id,
        activity_period_number,
        activity_start_date,
        activity_end_date
    FROM {{ ref('int_customer_activity_periods') }}

),

periods_with_next AS (

    SELECT
        customer_id,
        activity_period_number,
        activity_start_date,
        activity_end_date,

        LEAD(activity_start_date) OVER (
            PARTITION BY customer_id
            ORDER BY activity_start_date, activity_period_number
        ) AS next_activity_start_date

    FROM activity_periods

),

churn_events AS (

    SELECT
        customer_id,
        activity_period_number,
        activity_end_date AS churn_date,
        next_activity_start_date,

        CASE
            WHEN next_activity_start_date <= {{ as_of_date() }} THEN TRUE
            ELSE FALSE
        END AS is_reactivated,

        CASE
            WHEN next_activity_start_date <= {{ as_of_date() }}
            THEN DATEDIFF(
                DAY,
                activity_end_date,
                next_activity_start_date
            )
            ELSE NULL
        END AS days_until_reactivation

    FROM periods_with_next

    WHERE activity_end_date IS NOT NULL
      AND activity_end_date <= {{ as_of_date() }}

)

SELECT *
FROM churn_events
