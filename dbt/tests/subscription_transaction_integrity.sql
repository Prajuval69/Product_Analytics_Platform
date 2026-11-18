select t.transaction_id from {{ ref('stg_transactions') }} t join {{ ref('stg_subscriptions') }} s using(subscription_id)
where t.user_id<>s.user_id or t.product_id<>s.product_id or t.transaction_at<s.started_at
or (s.cancelled_at is not null and t.transaction_at>=s.cancelled_at)
