select e.event_id from {{ ref('stg_events') }} e join {{ ref('stg_users') }} u using(user_id)
left join {{ ref('stg_features') }} f using(feature_id) cross join {{ source('control','run_config') }} c
where e.event_at<u.signup_at or e.product_id<>u.product_id
 or (e.feature_id is not null and e.product_id<>f.product_id)
 or e.event_date<c.history_start or e.event_date>c.history_end
