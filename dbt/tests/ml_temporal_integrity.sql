select f.* from {{ ref('int_churn_features') }} f cross join {{ source('control','run_config') }} c
where (f.cutoff_date+30>c.history_end and f.churned is not null)
 or (f.cutoff_date+30<=c.history_end and f.churned is null)
 or f.tenure_days<30 or f.days_since_last_activity not between 0 and 29
 or f.active_days_30d not between 1 and 30 or f.subscription_tenure_days<0
