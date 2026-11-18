select * from {{ ref('mart_retention_cohorts') }} where retained_users>eligible_users or eligible_users>cohort_size
 or retention_rate not between 0 and 1
