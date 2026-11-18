with cohorts as (
 select u.*,date_trunc('month',u.signup_date)::date as cohort_month,offset_days,c.history_end
 from {{ ref('stg_users') }} u cross join {{ source('control','run_config') }} c
 cross join (values(1),(7),(30),(60),(90)) offsets(offset_days)
)
select md5(concat_ws(':',u.product_id,u.acquisition_channel,u.cohort_month,u.offset_days)) as cohort_key,
 u.product_id,u.acquisition_channel,u.cohort_month,u.offset_days,count(*) as cohort_size,
 count(*) filter(where u.signup_date+u.offset_days<=u.history_end) as eligible_users,
 count(a.user_id) as retained_users,
 count(a.user_id)::numeric/nullif(count(*) filter(where u.signup_date+u.offset_days<=u.history_end),0) as retention_rate
from cohorts u left join {{ ref('int_user_daily_activity') }} a on a.user_id=u.user_id
 and a.activity_date=u.signup_date+u.offset_days and a.activity_date<=u.history_end
group by 2,3,4,5
