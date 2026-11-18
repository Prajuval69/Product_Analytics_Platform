select md5('event:'||event_id::text) as event_key,{{ user_key('user_id') }} as user_key,
 {{ product_key('product_id') }} as product_key,{{ feature_key('feature_id') }} as feature_key,
 to_char(event_date,'YYYYMMDD')::int as date_key,* from {{ ref('stg_events') }}
