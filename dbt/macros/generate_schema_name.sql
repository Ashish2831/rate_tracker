{#
  Override dbt default schema naming (which would prefix target.schema + custom schema).
  With +schema: staging | intermediate | analytics in dbt_project.yml, use those names as-is:
    staging.stg_raw_responses
    intermediate.int_rates_parsed
    analytics.mart_rates
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
