select md5('ticket:'||ticket_id::text) as ticket_key,{{ user_key('user_id') }} as user_key,
 {{ product_key('product_id') }} as product_key,to_char(opened_at at time zone 'UTC','YYYYMMDD')::int as date_key,*
from {{ ref('stg_support_tickets') }}
