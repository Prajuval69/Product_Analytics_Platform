select d::date as date_day,to_char(d,'YYYYMMDD')::int as date_key,extract(isodow from d)::int as day_of_week,
 to_char(d,'Day') as day_name,date_trunc('week',d)::date as week_start,
 date_trunc('month',d)::date as month_start,extract(month from d)::int as month_number,
 extract(quarter from d)::int as quarter_number,extract(year from d)::int as year_number,
 extract(isodow from d) in (6,7) as is_weekend
from {{ source('control','run_config') }} c,
 lateral generate_series(c.history_start::timestamp,c.history_end::timestamp,interval '1 day') d
