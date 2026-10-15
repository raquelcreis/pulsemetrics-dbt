
-- Consolidate payment attempts into one record per
-- subscription and billing period.
--
-- A successful attempt takes precedence over failed or
-- refunded attempts when classifying the billing period.
-- Attempt amounts are not summed, avoiding duplicate revenue.

WITH payment_attempts AS (

    SELECT *
    FROM {{ ref('stg_payments') }}

),

billing_periods AS (

    SELECT
        subscription_id,
        billing_period_start_date,

        COUNT(*) AS attempts,

        COUNT_IF(status = 'PAID') AS successful_attempts,

        MIN(payment_datetime) AS first_attempt_at,

        MIN(
            CASE
                WHEN status = 'PAID' THEN payment_datetime
            END
        ) AS paid_at,

        CASE
            WHEN COUNT_IF(status = 'PAID') > 0
                THEN 'PAID'

            WHEN COUNT_IF(status = 'REFUNDED') > 0
                THEN 'REFUNDED'

            ELSE 'FAILED'
        END AS billing_status

    FROM payment_attempts

    GROUP BY
        subscription_id,
        billing_period_start_date

)

SELECT *
FROM billing_periods
