{% macro generate_schema_name(custom_schema_name, node) -%}
    {{ custom_schema_name | trim if custom_schema_name else target.schema }}
{%- endmacro %}

{% macro active_event(column) -%}
    {{ column }} in ('login','feature_used','search','report_created','export_completed','invite_sent','invite_accepted')
{%- endmacro %}

{% macro user_key(column) -%}md5('user:' || {{ column }}::text){%- endmacro %}
{% macro product_key(column) -%}md5('product:' || {{ column }}::text){%- endmacro %}
{% macro feature_key(column) -%}md5('feature:' || {{ column }}::text){%- endmacro %}

{% macro churn_outcome(cancelled_at, future_active_days, cutoff, horizon_end) -%}
    (coalesce({{ cancelled_at }} > {{ cutoff }} and {{ cancelled_at }} <= {{ horizon_end }}, false)
      or {{ future_active_days }} = 0)
{%- endmacro %}
