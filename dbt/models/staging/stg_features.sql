select feature_id, product_id, trim(feature_name) as feature_name, is_key_feature from {{ source('raw','features') }}
