
SELECT *
FROM {{ ref('int_customer_churn_events') }}
WHERE
    churn_date IS NULL
    OR churn_date > CURRENT_DATE()
    OR (
        is_reactivated = TRUE
        AND (
            next_activity_start_date IS NULL
            OR next_activity_start_date <= churn_date
        )
    )
