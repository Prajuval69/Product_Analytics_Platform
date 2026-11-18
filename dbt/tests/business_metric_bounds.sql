select * from {{ ref('mart_product_metrics') }}
where dau>wau or wau>mau or dau<0 or revenue<0 or mrr<0
 or activation_rate not between 0 and 1 or conversion_rate not between 0 and 1
 or churn_rate not between 0 and 1 or churned_users>churn_eligible
 or activated_users>activation_eligible or converted_users>funnel_eligible
