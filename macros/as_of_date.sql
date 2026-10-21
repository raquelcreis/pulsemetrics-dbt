
{#-
    Reference date for every "completed month" and "has already happened"
    rule in the project.

    Defaults to CURRENT_DATE(). Pass a fixed date to reproduce the metrics
    exactly as they were on that day:

        dbt build --vars '{"as_of_date": "2026-09-30"}'
-#}
{% macro as_of_date() -%}

    {%- set as_of = var('as_of_date', none) -%}

    {%- if as_of -%}
        '{{ as_of }}'::DATE
    {%- else -%}
        CURRENT_DATE()
    {%- endif -%}

{%- endmacro %}
