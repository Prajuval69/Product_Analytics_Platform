select md5('session:'||session_id) as session_key,{{ user_key('user_id') }} as user_key,
 {{ product_key('product_id') }} as product_key,to_char(session_date,'YYYYMMDD')::int as date_key,*
from {{ ref('int_user_sessions') }}
