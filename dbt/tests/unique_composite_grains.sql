select 'activity' as model from {{ ref('int_user_daily_activity') }} group by user_id,activity_date having count(*)>1
union all select 'feature_usage' from {{ ref('int_user_feature_usage') }} group by user_id,feature_id,usage_month having count(*)>1
union all select 'ml_features' from {{ ref('int_churn_features') }} group by user_id,cutoff_date having count(*)>1
