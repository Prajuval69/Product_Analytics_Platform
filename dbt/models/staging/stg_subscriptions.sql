select subscription_id, user_id, product_id, lower(trim(plan)) as plan,
 started_at, cancelled_at, monthly_price, lower(trim(status)) as status
from {{ source('raw','subscriptions') }}
