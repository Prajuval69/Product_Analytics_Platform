select {{ feature_key('feature_id') }} as feature_key,{{ product_key('product_id') }} as product_key,* from {{ ref('stg_features') }}
