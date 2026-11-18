with counts as (
 select f.product_id,f.acquisition_channel,f.country,f.plan,
 count(*) as entrants,count(onboarding_at) as onboarded,count(feature_at) as feature_users,count(purchase_at) as purchasers
 from {{ ref('int_user_funnel') }} f cross join {{ source('control','run_config') }} c
 where f.signup_date<=c.history_end-30 group by 1,2,3,4
), steps as (
 select c.*,s.step_number,s.step_name,s.users_at_step,
 lag(s.users_at_step) over(partition by product_id,acquisition_channel,country,plan order by step_number) as previous_users
 from counts c cross join lateral (values(1,'signup',entrants),(2,'onboarding_completed',onboarded),
 (3,'feature_used',feature_users),(4,'purchase_completed',purchasers)) s(step_number,step_name,users_at_step)
)
select md5(concat_ws(':',product_id,acquisition_channel,country,plan,step_number)) as funnel_key,
 product_id,acquisition_channel,country,plan,step_number,step_name,entrants,users_at_step,
 users_at_step::numeric/nullif(entrants,0) as conversion_rate,
 coalesce(previous_users-users_at_step,0) as dropoff_users,
 case when previous_users is not null then 1-users_at_step::numeric/nullif(previous_users,0) end as step_dropoff_rate
from steps
