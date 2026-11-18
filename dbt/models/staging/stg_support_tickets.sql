select ticket_id, user_id, product_id, opened_at, resolved_at, priority, category,
 extract(epoch from (resolved_at-opened_at))/3600.0 as resolution_hours
from {{ source('raw','support_tickets') }}
