# Canonical metric definitions

All dates are UTC. `C` denotes an inclusive observation date; timestamps observe strictly before midnight `C+1`. `history_end` is the final observed source date. The macro `active_event` in `dbt/macros/core.sql` centrally classifies qualifying events: login, feature_used, search, report_created, export_completed, invite_sent and invite_accepted. Signup, onboarding, feature_viewed, support_opened, purchase and churn_signal do not independently establish activity.

| Metric | Exact definition | Grain/window |
|---|---|---|
| DAU | Distinct users with qualifying activity on date D | Product/date |
| WAU | Distinct active users on dates D−6 through D inclusive | Rolling 7 calendar days |
| MAU | Distinct active users on dates D−29 through D inclusive | Rolling 30 calendar days |
| Activation | Users with feature_used at or after signup and strictly before signup+7 days / signups whose signup date ≤ D−7 | Cumulative mature signups by product/date |
| Ordered funnel | Signup → onboarding_completed → feature_used → purchase_completed, in timestamp order and strictly before signup+30 days | Product/channel/country/signup-plan/step; mature signups only |
| Funnel conversion | Users reaching a step / entrants; final purchasers / entrants is overall conversion | Mature signup population |
| Step dropoff | Previous-step count − current-step count; rate divides by previous-step count | Ordered adjacent steps |
| D1/D7/D30/D60/D90 retention | Users active on exactly signup_date+offset / cohort users with that target date observed | Signup month/product/channel/offset |
| Feature adoption | Distinct users using a feature in a calendar month / distinct active users of the same product and signup plan in that month | Feature/month/signup plan |
| Churn eligibility | Signup age ≥30 days, at least one active date in C−29…C, and no cancellation through C | Product/cutoff |
| Churn outcome | Eligible user cancels on dates C+1…C+30 **or** has zero qualifying activity on those dates | Future 30-day horizon |
| Daily reported churn | Churn outcomes at endpoint D / eligible users at C=D−30 | Fully observed trailing outcome window |
| Revenue | Sum invoice amounts with status succeeded on date D; failed attempts contribute zero | USD product/date |
| ARPU | Daily revenue / DAU on the same date and product | Null if DAU=0 |
| ARPPU | Daily revenue / distinct users with a successful invoice that date | Null if no paying users |
| MRR | Sum monthly list price of subscriptions started before end of D and not cancelled before that boundary | Contracted price snapshot, not revenue |
| Active subscriptions | Count subscriptions contributing to MRR | End-of-day snapshot |
| Customer segment | Lifetime successful revenue ≥500 USD: high_value; >0: paying; otherwise free | Current descriptive user snapshot |

No denominator means a null rate; a valid denominator with no success means zero. Cohort rows retain total cohort size separately from maturity-adjusted eligible count. Exact-day retention is sensitive to intermittent use and should not be described as rolling retention. A cancelled user may later have activity; cancellation still counts as a churn outcome. Already-cancelled customers are excluded from new prediction populations.

Current customer health distinguishes cancelled, inactive (no active date in the last 30 days), engaged (at least five active days), and at_risk. This descriptive status is **not** the forward-looking churn label and is never a predictor.

The subscription grain is one paid subscription per customer lifetime. Plan is assigned at signup and remains fixed; this simulation has no plan changes, refunds, currency conversion or multi-product customers. Payment cadence is 30 days; calendar-month feature adoption remains a calendar calculation.

Aggregation rules: sum revenue and distinct-product counts only when products contain disjoint user populations (true here); never sum DAU over dates. Compute aggregate rates with `SUM(numerator)/SUM(denominator)`, preserving filter alignment. For multi-date MAU, display a selected-date value rather than a sum. Threshold selection and risk bands are described separately in ML documentation.
