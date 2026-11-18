{{ config(indexes=[{'columns':['user_id','cutoff_date'],'unique':true}]) }}
with cutoffs as (
 select history_end-offset_days as cutoff_date,history_end from {{ source('control','run_config') }}
 cross join (values(150),(90),(30),(0)) offsets(offset_days)
), eligible as (
 select u.*,c.cutoff_date,c.history_end,(c.cutoff_date+1)::timestamp at time zone 'UTC' as cutoff_at,
 (c.cutoff_date+31)::timestamp at time zone 'UTC' as horizon_end_at,sub.started_at,sub.cancelled_at
 from {{ ref('stg_users') }} u cross join cutoffs c left join {{ ref('stg_subscriptions') }} sub using(user_id)
 where u.signup_date <= c.cutoff_date-30
 and (sub.cancelled_at is null or sub.cancelled_at >= (c.cutoff_date+1)::timestamp at time zone 'UTC')
 and exists(select 1 from {{ ref('int_user_daily_activity') }} a where a.user_id=u.user_id
 and a.activity_date > c.cutoff_date-30 and a.activity_date <= c.cutoff_date)
), features as (
 select e.user_id,e.product_id,e.cutoff_date,e.history_end,e.plan,e.cutoff_at,e.horizon_end_at,e.cancelled_at,
 e.cutoff_date-e.signup_date as tenure_days,
 coalesce(a.sessions_30d,0) as sessions_30d,coalesce(a.active_days_30d,0) as active_days_30d,
 coalesce(a.event_count_30d,0) as event_count_30d,e.cutoff_date-a.last_activity_date as days_since_last_activity,
 coalesce(f.feature_diversity,0) as feature_diversity,coalesce(f.key_feature_uses,0) as key_feature_uses,
 coalesce(t.revenue_30d,0) as revenue_30d,coalesce(s.support_tickets_30d,0) as support_tickets_30d,
 coalesce(extract(day from(e.cutoff_at-e.started_at)),0) as subscription_tenure_days,
 coalesce(a.future_active_days,0) as future_active_days
 from eligible e
 left join lateral (
  select sum(sessions) filter(where activity_date<=e.cutoff_date) as sessions_30d,
  count(*) filter(where activity_date<=e.cutoff_date) as active_days_30d,
  sum(active_event_count) filter(where activity_date<=e.cutoff_date) as event_count_30d,
  max(activity_date) filter(where activity_date<=e.cutoff_date) as last_activity_date,
  count(*) filter(where activity_date>e.cutoff_date) as future_active_days
  from {{ ref('int_user_daily_activity') }} where user_id=e.user_id
  and activity_date > e.cutoff_date-30 and activity_date <= e.cutoff_date+30
 ) a on true
 left join lateral (
  select count(distinct feature_id) as feature_diversity,
  count(*) filter(where feature_id=(e.product_id-1)*3+1) as key_feature_uses
  from {{ ref('stg_events') }} where user_id=e.user_id and event_type='feature_used'
  and event_at >= e.cutoff_at-interval '30 days' and event_at<e.cutoff_at
 ) f on true
 left join lateral (
  select sum(recognized_revenue) as revenue_30d from {{ ref('stg_transactions') }}
  where user_id=e.user_id and transaction_at>=e.cutoff_at-interval '30 days' and transaction_at<e.cutoff_at
 ) t on true
 left join lateral (
  select count(*) as support_tickets_30d from {{ ref('stg_support_tickets') }}
  where user_id=e.user_id and opened_at>=e.cutoff_at-interval '30 days' and opened_at<e.cutoff_at
 ) s on true
)
select user_id,product_id,cutoff_date,plan,tenure_days,sessions_30d,active_days_30d,event_count_30d,
 days_since_last_activity,feature_diversity,key_feature_uses,revenue_30d,support_tickets_30d,
 greatest(subscription_tenure_days,0) as subscription_tenure_days,
 case when cutoff_date+30 <= history_end then
 {{ churn_outcome('cancelled_at','future_active_days',"cutoff_at - interval '1 microsecond'", "horizon_end_at - interval '1 microsecond'") }}::int end as churned
from features
