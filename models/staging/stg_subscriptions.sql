WITH source AS (

    SELECT *
    FROM {{ source('raw', 'subscriptions') }}

),

renamed AS (

    SELECT
        TRIM(subscription_id) AS subscription_id,
        TRIM(customer_id) AS customer_id,
        TRIM(plan_id) AS plan_id,
        start_date::DATE AS start_date,
        end_date::DATE AS end_date,
        created_at::TIMESTAMP_NTZ AS created_at

    FROM source

)

SELECT *
FROM renamed
