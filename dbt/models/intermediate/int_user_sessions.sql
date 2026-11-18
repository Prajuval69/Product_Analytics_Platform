select session_id, user_id, product_id, min(event_at) as session_start,
 max(event_at) as session_end, min(event_date) as session_date, min(device) as device,
 count(*) as event_count, bool_or(is_active) as is_active,
 extract(epoch from(max(event_at)-min(event_at))) as duration_seconds
from {{ ref('stg_events') }} group by 1,2,3
