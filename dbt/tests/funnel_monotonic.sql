with steps as (
 select *,lag(users_at_step) over(partition by product_id,acquisition_channel,country,plan order by step_number) as previous
 from {{ ref('mart_funnel_analysis') }}
)
select * from steps where users_at_step>previous or conversion_rate not between 0 and 1
