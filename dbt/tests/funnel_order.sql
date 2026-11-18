select * from {{ ref('int_user_funnel') }}
where onboarding_at<signup_at or feature_at<onboarding_at or purchase_at<feature_at
 or (feature_at is not null and onboarding_at is null)
 or (purchase_at is not null and feature_at is null)
 or purchase_at>=signup_at+interval '30 days'
 or activation_at>=signup_at+interval '7 days'
