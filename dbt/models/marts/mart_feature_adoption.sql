with denominators as (
 select a.product_id,date_trunc('month',a.activity_date)::date as usage_month,u.plan,
 count(distinct a.user_id) as eligible_active_users
 from {{ ref('int_user_daily_activity') }} a join {{ ref('stg_users') }} u using(user_id) group by 1,2,3
), usage as (
 select feature_id,usage_month,plan,count(*) as adopted_users,sum(use_count) as use_count
 from {{ ref('int_user_feature_usage') }} group by 1,2,3
)
select md5(concat_ws(':',f.feature_id,d.usage_month,d.plan)) as adoption_key,
 f.product_id,f.feature_id,f.feature_name,d.usage_month,d.plan,d.eligible_active_users,
 coalesce(u.adopted_users,0) as adopted_users,coalesce(u.use_count,0) as use_count,
 coalesce(u.adopted_users,0)::numeric/nullif(d.eligible_active_users,0) as adoption_rate
from denominators d join {{ ref('stg_features') }} f using(product_id)
left join usage u on u.feature_id=f.feature_id and u.usage_month=d.usage_month and u.plan=d.plan
