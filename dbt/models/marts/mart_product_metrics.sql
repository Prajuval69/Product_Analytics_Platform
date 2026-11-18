with calendar as (
 select d.date_day as metric_date,p.product_id from {{ ref('dim_date') }} d cross join {{ ref('stg_products') }} p
), activity as materialized (
 select c.metric_date,c.product_id,count(distinct a.user_id) filter(where a.activity_date=c.metric_date) as dau,
 count(distinct a.user_id) filter(where a.activity_date>c.metric_date-7) as wau,
 count(distinct a.user_id) as mau
 from calendar c left join {{ ref('int_user_daily_activity') }} a on a.product_id=c.product_id
 and a.activity_date>c.metric_date-30 and a.activity_date<=c.metric_date group by 1,2
), lifecycle as materialized (
 select c.metric_date,c.product_id,
 count(*) filter(where f.signup_date<=c.metric_date-7) as activation_eligible,
 count(*) filter(where f.signup_date<=c.metric_date-7 and f.activation_at is not null) as activated_users,
 count(*) filter(where f.signup_date<=c.metric_date-30) as funnel_eligible,
 count(*) filter(where f.signup_date<=c.metric_date-30 and f.purchase_at is not null) as converted_users
 from calendar c left join {{ ref('int_user_funnel') }} f on f.product_id=c.product_id and f.signup_date<=c.metric_date group by 1,2
), churn as materialized (
 select c.metric_date,c.product_id,count(u.user_id) as churn_eligible,
 count(u.user_id) filter(where {{ churn_outcome('s.cancelled_at', 'future.active_days', "((c.metric_date-29)::timestamp at time zone 'UTC') - interval '1 microsecond'", "((c.metric_date+1)::timestamp at time zone 'UTC') - interval '1 microsecond'") }}) as churned_users
 from calendar c left join {{ ref('stg_users') }} u on u.product_id=c.product_id and u.signup_date<=c.metric_date-60
 and exists(select 1 from {{ ref('int_user_daily_activity') }} a where a.user_id=u.user_id
 and a.activity_date>c.metric_date-60 and a.activity_date<=c.metric_date-30)
 and not exists(select 1 from {{ ref('stg_subscriptions') }} s where s.user_id=u.user_id
 and s.cancelled_at < (c.metric_date-29)::timestamp at time zone 'UTC')
 left join {{ ref('stg_subscriptions') }} s on s.user_id=u.user_id
 left join lateral (select count(*) as active_days from {{ ref('int_user_daily_activity') }} a
 where a.user_id=u.user_id and a.activity_date>c.metric_date-30 and a.activity_date<=c.metric_date) future on true
 group by 1,2
), revenue as materialized (
 select product_id,transaction_date,sum(recognized_revenue) as revenue,
 count(*) filter(where status='succeeded') as transactions,
 count(distinct user_id) filter(where status='succeeded') as paying_users
 from {{ ref('stg_transactions') }} group by 1,2
), mrr as materialized (
 select c.metric_date,c.product_id,coalesce(sum(s.monthly_price),0) as mrr,count(s.subscription_id) as active_subscriptions
 from calendar c left join {{ ref('stg_subscriptions') }} s on s.product_id=c.product_id
 and s.started_at < (c.metric_date+1)::timestamp at time zone 'UTC'
 and (s.cancelled_at is null or s.cancelled_at >= (c.metric_date+1)::timestamp at time zone 'UTC') group by 1,2
)
select md5(concat_ws(':',c.product_id,c.metric_date)) as metric_key,c.metric_date,c.product_id,
 a.dau,a.wau,a.mau,l.activation_eligible,l.activated_users,
 l.activated_users::numeric/nullif(l.activation_eligible,0) as activation_rate,
 l.funnel_eligible,l.converted_users,l.converted_users::numeric/nullif(l.funnel_eligible,0) as conversion_rate,
 h.churn_eligible,h.churned_users,h.churned_users::numeric/nullif(h.churn_eligible,0) as churn_rate,
 coalesce(r.revenue,0) as revenue,coalesce(r.transactions,0) as paid_transactions,
 coalesce(r.paying_users,0) as paying_users,coalesce(r.revenue,0)/nullif(a.dau,0) as arpu,
 coalesce(r.revenue,0)/nullif(r.paying_users,0) as arppu,m.mrr,m.active_subscriptions
from calendar c join activity a using(metric_date,product_id) join lifecycle l using(metric_date,product_id)
join churn h using(metric_date,product_id) left join revenue r on r.product_id=c.product_id and r.transaction_date=c.metric_date
join mrr m on m.metric_date=c.metric_date and m.product_id=c.product_id
