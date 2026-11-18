select {{ product_key('product_id') }} as product_key,* from {{ ref('stg_products') }}
