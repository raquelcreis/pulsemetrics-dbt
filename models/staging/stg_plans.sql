WITH source AS (

    SELECT *
    FROM {{ source('raw', 'plans') }}

),

renamed AS (

    SELECT
        TRIM(plan_id) AS plan_id,
        TRIM(plan_name) AS plan_name,
        monthly_price::NUMBER(18, 2) AS monthly_price,
        UPPER(TRIM(billing_cycle)) AS billing_cycle

    FROM source

)

SELECT *
FROM renamed
