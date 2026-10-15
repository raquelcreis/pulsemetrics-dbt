
WITH source AS (

    SELECT *
    FROM {{ source('raw', 'customers') }}

),

renamed AS (

    SELECT
        id AS customer_id,
        TRIM(customer_name) AS customer_name,
        document,
        LOWER(TRIM(email)) AS email,
        TRIM(country) AS country_raw,
        created_at::TIMESTAMP_NTZ AS created_at

    FROM source

)

SELECT *
FROM renamed