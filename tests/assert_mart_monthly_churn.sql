
SELECT *
FROM {{ ref('mart_monthly_churn') }}
WHERE
    opening_active_customers < 0
    OR churned_customers < 0
    OR churned_customers > opening_active_customers
    OR customer_churn_rate < 0
    OR customer_churn_rate > 1
    OR ABS(
        customer_churn_rate
        - churned_customers::FLOAT
            / NULLIF(opening_active_customers, 0)
    ) > 0.000001
