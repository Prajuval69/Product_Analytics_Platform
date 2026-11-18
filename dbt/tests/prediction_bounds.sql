select * from {{ ref('mart_churn_predictions') }} where churn_probability not between 0 and 1
 or risk_band <> case when churn_probability>=0.7 then 'high' when churn_probability>=0.3 then 'medium' else 'low' end
