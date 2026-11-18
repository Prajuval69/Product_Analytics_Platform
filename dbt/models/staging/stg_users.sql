select user_id, product_id, signup_at, (signup_at at time zone 'UTC')::date as signup_date,
 lower(trim(acquisition_channel)) as acquisition_channel, upper(trim(country)) as country,
 lower(trim(plan)) as plan, lower(trim(device)) as device
from {{ source('raw','users') }}
