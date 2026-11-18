select md5('subscription:'||subscription_id::text) as subscription_key,{{ user_key('user_id') }} as user_key,
 {{ product_key('product_id') }} as product_key,to_char(started_at at time zone 'UTC','YYYYMMDD')::int as date_key,*
from {{ ref('stg_subscriptions') }}
