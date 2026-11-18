with onboarding as (
 select u.*, min(e.event_at) filter(where e.event_type='onboarding_completed'
   and e.event_at >= u.signup_at and e.event_at < u.signup_at+interval '30 days') as onboarding_at,
 min(e.event_at) filter(where e.event_type='feature_used' and e.event_at >= u.signup_at
   and e.event_at < u.signup_at+interval '7 days') as activation_at
 from {{ ref('stg_users') }} u left join {{ ref('stg_events') }} e using(user_id)
 group by u.user_id,u.product_id,u.signup_at,u.signup_date,u.acquisition_channel,u.country,u.plan,u.device
), usage as (
 select o.*, (select min(e.event_at) from {{ ref('stg_events') }} e
 where e.user_id=o.user_id and e.event_type='feature_used' and e.event_at >= o.onboarding_at
 and e.event_at < o.signup_at+interval '30 days') as feature_at from onboarding o
)
select u.*, (select min(e.event_at) from {{ ref('stg_events') }} e
 where e.user_id=u.user_id and e.event_type='purchase_completed' and e.event_at >= u.feature_at
 and e.event_at < u.signup_at+interval '30 days') as purchase_at
from usage u
