{{ config(materialized='view') }}
select {{ user_key('p.user_id') }} as user_key,p.*,u.product_id,u.plan,u.acquisition_channel,u.country,
 h.customer_segment
from {{ source('control','ml_predictions') }} p join {{ ref('stg_users') }} u using(user_id)
join {{ ref('int_customer_health') }} h using(user_id)
