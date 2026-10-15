
WITH customer_revenue AS (

    SELECT
        customer_id,
        month_start,
        active_subscriptions,
        contracted_mrr
    FROM {{ ref('int_customer_revenue') }}

),

monthly_revenue AS (

    SELECT
        month_start,
        COUNT(DISTINCT customer_id) AS active_customers,
        SUM(active_subscriptions) AS active_subscriptions,
        SUM(contracted_mrr) AS contracted_mrr
    FROM customer_revenue
    GROUP BY month_start

)

SELECT
    month_start,
    active_customers,
    active_subscriptions,
    contracted_mrr,
    contracted_mrr / NULLIF(active_customers, 0) AS arpa
FROM monthly_revenue
