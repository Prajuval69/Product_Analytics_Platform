select 1 as mismatch where
 (select coalesce(sum(revenue),0) from {{ ref('mart_product_metrics') }}) <>
 (select coalesce(sum(recognized_revenue),0) from {{ ref('fct_transactions') }})
