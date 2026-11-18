select {{ user_key('user_id') }} as user_key,* from {{ ref('int_customer_health') }}
