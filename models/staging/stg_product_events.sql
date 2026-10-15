WITH source AS (

    SELECT *
    FROM {{ source('raw', 'product_events') }}

),

renamed AS (

    SELECT
        TRIM(event_id) AS event_id,
        TRIM(customer_id) AS customer_id,
        UPPER(TRIM(event_type)) AS event_type,
        event_timestamp::TIMESTAMP_NTZ AS event_timestamp,
        event_properties,
        created_at::TIMESTAMP_NTZ AS created_at

    FROM source

)

SELECT *
FROM renamed
