SELECT *
FROM {{ ref('int_subscription_periods') }}
WHERE
    month_start >= DATE_TRUNC('MONTH', {{ as_of_date() }})
    OR start_date >= DATEADD(MONTH, 1, month_start)
    OR (
        end_date IS NOT NULL
        AND end_date < DATEADD(MONTH, 1, month_start)
    )
