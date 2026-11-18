select md5('transaction:'||transaction_id::text) as transaction_key,{{ user_key('user_id') }} as user_key,
 {{ product_key('product_id') }} as product_key,to_char(transaction_date,'YYYYMMDD')::int as date_key,*
from {{ ref('stg_transactions') }}
