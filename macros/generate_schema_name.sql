
{#-
    Custom schema naming for PulseMetrics.

    The default dbt behavior concatenates the target schema
    with the custom schema (e.g., STAGING_STAGING).

    This macro returns the configured schema directly, keeping
    the project architecture organized into STAGING,
    INTERMEDIATE, and MARTS.
-#}
{% macro generate_schema_name(custom_schema_name, node) -%}

    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}

{%- endmacro %}
