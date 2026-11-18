{{ config(indexes=[{'columns':['user_id','activity_date'],'unique':true},{'columns':['product_id','activity_date']}]) }}
select user_id, product_id, event_date as activity_date, count(*) as active_event_count,
 count(distinct session_id) as sessions, count(distinct feature_id) as feature_diversity,
 min(event_at) as first_event_at, max(event_at) as last_event_at
from {{ ref('stg_events') }} where is_active
group by 1,2,3
