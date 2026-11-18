select {{ user_key('user_id') }} as user_key,{{ product_key('product_id') }} as product_key,
 user_id,product_id,signup_at,signup_date,acquisition_channel,country,plan,device,lifecycle_status,customer_segment
from {{ ref('int_customer_health') }}
