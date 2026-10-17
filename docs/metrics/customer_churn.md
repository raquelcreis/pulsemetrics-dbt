# Customer Churn — Definition & Methodology

## 1. Business definition

PulseMetrics has no explicit, reliable cancellation event. Customer churn is therefore an estimate based on subscription lifecycle dates, not an observed cancellation metric.

## 2. Activity periods and churn events

Subscription validity follows `[start_date, end_date)`: the start date is inclusive and the end date is exclusive. A null `end_date` represents an open-ended subscription.

The models combine each customer's subscription intervals into continuous activity periods. Overlapping subscriptions and same-day transitions remain one period, so a plan change alone does not count as churn. A positive gap between periods produces a churn event at the end of the prior activity period. A later period is a realized reactivation only when its start date is on or before `CURRENT_DATE()`; a future-dated period does not yet count as a reactivation. Future end dates are not realized churn events.

Because an end date may represent an upgrade or downgrade, a gap is a lifecycle-based churn proxy and does not prove cancellation or loss of access.

## 3. Monthly churn rate

The mart contains completed calendar months only. For each month:

- Opening base: distinct customers active immediately before the month began.
- Churned customers: opening-base customers whose activity period ends during that month.
- Churn rate: churned opening-base customers divided by the opening base.

Customers who start and end activity within the same month are excluded from that month's opening-base churn rate. The current incomplete month is excluded. Reactivations do not erase the earlier churn event; they begin a later activity period and can support a future churn event.

## 4. Limitations

- The data does not identify cancellation reasons or confirm that access ended.
- Missing or inaccurate subscription records can change inferred activity periods.
- The rate is an opening-base customer churn rate, not a subscription churn rate or a payment-based cancellation rate.
- A customer may have multiple lifecycle-based churn events after separate periods of activity.

## 5. dbt implementation

`int_customer_activity_periods` merges subscription intervals per customer. `int_customer_churn_events` emits completed activity-period ends and realized reactivation metadata. `mart_monthly_churn` applies the opening-base definition and includes completed months only.
