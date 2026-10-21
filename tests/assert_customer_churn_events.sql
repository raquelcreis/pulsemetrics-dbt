
SELECT *
FROM {{ ref('int_customer_churn_events') }}
WHERE
    churn_date IS NULL
    OR churn_date > {{ as_of_date() }}
    OR is_reactivated IS NULL
    OR (
        is_reactivated = TRUE
        AND (
            next_activity_start_date IS NULL
            OR next_activity_start_date <= churn_date
            OR next_activity_start_date > {{ as_of_date() }}
            OR days_until_reactivation IS NULL
            OR days_until_reactivation != DATEDIFF(
                DAY, churn_date, next_activity_start_date
            )
        )
    )
    OR (
        is_reactivated = FALSE
        AND (
            next_activity_start_date <= {{ as_of_date() }}
            OR days_until_reactivation IS NOT NULL
        )
    )
