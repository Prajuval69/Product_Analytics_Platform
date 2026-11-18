select u.user_id, u.product_id,
 coalesce(sum(t.recognized_revenue),0) as lifetime_revenue,
 count(t.transaction_id) filter(where t.status='succeeded') as paid_transactions,
 max(t.transaction_at) filter(where t.status='succeeded') as last_payment_at
from {{ ref('stg_users') }} u left join {{ ref('stg_transactions') }} t using(user_id)
group by 1,2
