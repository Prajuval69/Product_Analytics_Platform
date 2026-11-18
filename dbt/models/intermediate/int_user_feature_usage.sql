select e.user_id, e.product_id, e.feature_id, date_trunc('month',e.event_date)::date as usage_month,
 u.plan, count(*) as use_count, min(e.event_at) as first_used_at, max(e.event_at) as last_used_at
from {{ ref('stg_events') }} e join {{ ref('stg_users') }} u using(user_id)
where e.event_type='feature_used'
group by 1,2,3,4,5
