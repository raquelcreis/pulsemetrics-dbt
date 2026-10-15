
SELECT
    month_start,
    active_customers,
    contracted_mrr,
    arpa
FROM {{ ref('mart_monthly_revenue') }}
WHERE
    active_customers <= 0
    OR ABS(
        arpa - (contracted_mrr / NULLIF(active_customers, 0))
    ) > 0.01
