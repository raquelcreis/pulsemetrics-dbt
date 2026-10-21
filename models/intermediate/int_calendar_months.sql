
-- One row per calendar month, from the first subscription month
-- through the last completed month before the as-of date.
--
-- Shared by the revenue and churn models so both use the same
-- reporting months without a hardcoded row limit.

WITH months AS (

    {{ dbt_utils.date_spine(
        datepart="month",
        start_date="(SELECT DATE_TRUNC('MONTH', MIN(start_date))::DATE FROM " ~ ref('stg_subscriptions') ~ ")",
        end_date="DATE_TRUNC('MONTH', " ~ as_of_date() ~ ")::DATE"
    ) }}

)

SELECT
    date_month::DATE AS month_start
FROM months
-- Completed months only; the as-of month itself is still in progress.
WHERE date_month < DATE_TRUNC('MONTH', {{ as_of_date() }})
