select transaction_id, subscription_id, user_id, product_id, transaction_at,
 (transaction_at at time zone 'UTC')::date as transaction_date, amount, upper(currency) as currency,
 status, case when status='succeeded' then amount else 0 end as recognized_revenue
from {{ source('raw','transactions') }}
