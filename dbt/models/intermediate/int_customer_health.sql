with activity as (
 select a.user_id, max(a.activity_date) as last_activity_date,
 sum(a.sessions) filter(where a.activity_date > c.history_end-30) as sessions_30d,
 count(*) filter(where a.activity_date > c.history_end-30) as active_days_30d
 from {{ ref('int_user_daily_activity') }} a cross join {{ source('control','run_config') }} c group by 1
), support as (
 select user_id,count(*) as ticket_count,count(*) filter(where resolved_at is null) as open_tickets
 from {{ ref('stg_support_tickets') }} group by 1
)
select u.*, c.history_end as as_of_date, a.last_activity_date,
 coalesce(a.sessions_30d,0) as sessions_30d,coalesce(a.active_days_30d,0) as active_days_30d,
 r.lifetime_revenue, coalesce(s.ticket_count,0) as ticket_count,coalesce(s.open_tickets,0) as open_tickets,
 case when sub.cancelled_at is not null then 'cancelled'
      when coalesce(a.last_activity_date,u.signup_date) <= c.history_end-30 then 'inactive'
      when coalesce(a.active_days_30d,0) >= 5 then 'engaged' else 'at_risk' end as lifecycle_status,
 case when r.lifetime_revenue >= 500 then 'high_value' when r.lifetime_revenue > 0 then 'paying' else 'free' end as customer_segment
from {{ ref('stg_users') }} u cross join {{ source('control','run_config') }} c
left join activity a using(user_id) left join {{ ref('int_user_revenue') }} r using(user_id)
left join support s using(user_id) left join {{ ref('stg_subscriptions') }} sub using(user_id)
