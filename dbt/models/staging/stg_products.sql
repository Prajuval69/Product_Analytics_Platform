select product_id, trim(product_name) as product_name, category from {{ source('raw','products') }}
