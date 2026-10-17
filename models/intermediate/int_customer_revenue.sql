
-- Calculate month-end contracted monthly recurring revenue per customer.
--
-- Grain: one row per customer and calendar month.
-- Input subscription periods are month-end snapshots. Revenue is based
-- on monthly plan prices, not payment attempts or payment status.

WITH subscription_months AS (

    SELECT
        subscription_id,
        customer_id,
        plan_id,
        month_start
    FROM {{ ref('int_subscription_periods') }}

),

plans AS (

    SELECT
        plan_id,
        monthly_price,
        billing_cycle
    FROM {{ ref('stg_plans') }}

),

customer_monthly_revenue AS (

    SELECT
        sm.customer_id,
        sm.month_start,

        COUNT(DISTINCT sm.subscription_id)
            AS active_subscriptions,

        SUM(
            CASE
                WHEN p.billing_cycle = 'MONTHLY'
                    THEN p.monthly_price
                ELSE NULL
            END
        ) AS contracted_mrr

    FROM subscription_months AS sm

    LEFT JOIN plans AS p
        ON sm.plan_id = p.plan_id

    GROUP BY
        sm.customer_id,
        sm.month_start

)

SELECT
    customer_id,
    month_start,
    active_subscriptions,
    contracted_mrr
FROM customer_monthly_revenue
