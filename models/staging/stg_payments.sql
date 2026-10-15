WITH source AS (

    SELECT *
    FROM {{ source('raw', 'payments') }}

),

renamed AS (

    SELECT
        TRIM(payment_id) AS payment_id,
        TRIM(subscription_id) AS subscription_id,
        billing_period_start_date::DATE
            AS billing_period_start_date,
        payment_datetime::TIMESTAMP_NTZ
            AS payment_datetime,
        amount::NUMBER(18, 2) AS amount,
        UPPER(TRIM(currency)) AS currency,
        UPPER(TRIM(status)) AS status,
        UPPER(TRIM(payment_method)) AS payment_method,
        created_at::TIMESTAMP_NTZ AS created_at

    FROM source

)

SELECT *
FROM renamed
