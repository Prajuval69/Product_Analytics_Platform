# Power BI dashboard build guide

The pipeline generates analytical CSVs; this repository does not claim a PBIX, screenshots or a published Power BI report. Use Power BI Desktop manually after a successful pipeline. Import files from `outputs/bi/` using **Get Data → Text/CSV**; keep identifiers as whole numbers, MD5 keys as text, dates as Date and rates/probabilities as Decimal Number. Currency is USD. Empty rate/score cells are null, not zero. Convert UTC timestamp text deliberately rather than relying on regional date parsing.

## Semantic model

Start with `dim_product` and `dim_date`. Link product_id 1:* from dim_product to executive_kpis, product_funnel, retention_cohorts, feature_adoption, customer_health, churn_predictions, revenue_subscriptions and subscriptions. Use single-direction filtering. Link date_day 1:* to executive_kpis.metric_date and revenue_subscriptions.transaction_date. Avoid duplicate product relationships via both user and feature dimensions on the same flat extract.

Use `dim_user.user_id` 1:* to revenue_subscriptions.user_id for signup plan/channel/country/device slicing; its plan is immutable. `customer_health.user_id` is unique, and its flattened prediction columns make a separate health-to-prediction relationship unnecessary. An optional normalized semantic model can use user_key and product_key in dimensions/subscriptions; the recommended flat reporting model avoids multiple relationship paths.

Retention cohort_month and adoption usage_month are monthly cohort/usage roles; use separate month dimensions or table-specific month slicers. Funnel describes all mature signups in the configured history, with no daily date key. Its title must state the mature population and source horizon.

## Pages and visuals

| Page | Datasets | Layout and interpretation |
|---|---|---|
| Executive Product Overview | executive_kpis, retention_cohorts | Selected-date DAU/WAU/MAU/MRR cards; weighted activation/conversion/churn cards; revenue line; activity lines; D7/D30 cohort trend |
| Product Funnel | product_funnel | Ordered signup/onboard/use/purchase funnel; step dropoff bars; channel comparison; plan/country/product slicers |
| Retention | retention_cohorts | Heatmap rows=cohort_month, columns=offset_days, color=weighted retention; eligible/cohort size; D1/D7/D30 trend; product/channel slicers |
| Feature Adoption | feature_adoption | Feature ranking by weighted adoption; adopted/eligible counts; usage trend; month/product/plan slicers |
| Customer Health | customer_health, churn_predictions | Risk-band counts; high-risk users; active_days_30d vs lifetime_revenue scatter; support/open-ticket indicators; segment/plan/channel/country/product slicers |
| Revenue & Subscription | revenue_subscriptions, executive_kpis, subscriptions | Revenue trend; selected-date MRR; plan mix; successful/failed volume; revenue by product/channel; cancellation dates/tenure |
| Data Quality | data_quality | Passed/failed counts; completeness; ingestion freshness; source history end; row counts; pipeline_status and checked_at |

The health export contains all users, including ineligible users with null risk. Label them “not scored” rather than low risk. Show scoring_date on the health page. Freshness refers to operational loaded_at; source_history_end is the synthetic horizon.

## Suggested DAX

```dax
Revenue = SUM(executive_kpis[revenue])
DAU = SUM(executive_kpis[dau])
WAU = SUM(executive_kpis[wau])
MAU = SUM(executive_kpis[mau])
Activation Rate = DIVIDE(SUM(executive_kpis[activated_users]), SUM(executive_kpis[activation_eligible]))
Conversion Rate = DIVIDE(SUM(executive_kpis[converted_users]), SUM(executive_kpis[funnel_eligible]))
Churn Rate = DIVIDE(SUM(executive_kpis[churned_users]), SUM(executive_kpis[churn_eligible]))
Daily ARPU = DIVIDE([Revenue], [DAU])
MRR = SUM(executive_kpis[mrr])
Retention Rate = DIVIDE(SUM(retention_cohorts[retained_users]), SUM(retention_cohorts[eligible_users]))
Feature Adoption Rate = DIVIDE(SUM(feature_adoption[adopted_users]), SUM(feature_adoption[eligible_active_users]))
Funnel Conversion = DIVIDE(SUM(product_funnel[users_at_step]), SUM(product_funnel[entrants]))
Failed Checks = COUNTROWS(FILTER(data_quality, data_quality[passed] = FALSE()))
```

DAU/WAU/MAU/MRR require one date per line point/card. Products are disjoint, allowing same-date sums across products. Multi-date ARPU is revenue per active-user-day, so enforce single-date selection for daily ARPU. Retention must filter one offset; adoption one feature; funnel conversion one step. Funnel entrants repeat across steps: never sum entrants over all four steps.

For a selected date range, cards can use `CALCULATE([MAU], LASTDATE(dim_date[date_day]))`; use the same final-date rule for MRR. Rate tooltips should show numerator/denominator.

## Slicer coverage

* Product: all analytical pages.
* Date: executive and revenue; separate month selectors for retention/adoption.
* Plan: funnel, adoption, health, predictions and revenue/subscriptions.
* Channel: funnel, retention, health, predictions and revenue via user attributes.
* Geography: funnel, health, predictions and revenue via user attributes.
* Device: health/user-based revenue only. Executive/retention/adoption marts are not device-grained; a device slicer must not imply otherwise.

Use consistent UTC/date labels, percentage formatting and a visible synthetic-data subtitle. Reserve red for failed checks/high risk and use a sequential cohort palette. Validate imported totals against `outputs/verification/pipeline_verification.json` before describing a report as verified. No actual Power BI report assembly was executed on this host.
