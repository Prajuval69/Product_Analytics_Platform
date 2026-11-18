select * from {{ ref('mart_feature_adoption') }} where adopted_users>eligible_active_users or adoption_rate not between 0 and 1
