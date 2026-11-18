select event_id, user_id, product_id, feature_id, session_id, event_at,
 (event_at at time zone 'UTC')::date as event_date, lower(trim(event_type)) as event_type,
 lower(trim(device)) as device, properties, {{ active_event('event_type') }} as is_active
from {{ source('raw','events') }}
