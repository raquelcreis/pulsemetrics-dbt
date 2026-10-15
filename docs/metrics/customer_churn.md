# Customer Churn — Definition & Methodology

## 1. Business definition

Customer churn occurs when a customer no longer has any active subscription.

PulseMetrics does not have an explicit, reliable field identifying customer cancellation events. Therefore, customer churn is estimated using a proxy derived from subscription lifecycle data.

## 2. Proxy methodology

The churn date is identified as the date on which a customer has no active subscriptions remaining.

The analysis uses the following source fields:

- `customer_id`: identifies the customer.
- `subscription_id`: identifies each subscription.
- `start_date`: beginning of the subscription validity period.
- `end_date`: end of the subscription validity period.

Subscription validity follows the interval `[start_date, end_date)`: the start date is inclusive and the end date is exclusive. A subscription with a null `end_date` is treated as having no recorded end date.

The proxy is based on the combined lifecycle of all subscriptions belonging to a customer, rather than on individual subscription termination events.

## 3. Business rules

1. Ending one subscription does not count as customer churn if another subscription remains active.
2. Customer churn occurs when the last active subscription ends and no other subscription is active from that date onward.
3. If a customer starts another subscription after a period without active subscriptions, the customer is considered reactivated. The previous churn event remains part of the historical record.
4. A subscription ending on the same date another subscription starts does not create a gap in customer activity.
5. Customers with no recorded subscription end date are not considered churned solely on that basis.
6. Future end dates must not be counted as realized churn events before their effective date.

## 4. Limitations and assumptions

This is an analytical proxy, not a directly observed cancellation event.

- The source data does not explicitly identify cancellation reasons.
- An end date may represent a subscription lifecycle transition, such as an upgrade or downgrade, rather than a customer's departure.
- The method assumes that subscription start and end dates accurately represent periods of customer access.
- Data quality issues or missing subscription records may affect the estimated churn date.
- A customer who churns and later returns can generate more than one churn event over time.

## 5. Interpretation

Metrics derived from this method should be described as estimated customer churn based on subscription lifecycle data.

The methodology should be revisited if reliable cancellation events, cancellation reasons, or customer status history become available.

## 6. dbt implementation

The transformation should identify customer-level periods of activity by combining all subscription validity intervals for each customer. Churn events are then derived from the end of an active period when no other subscription overlaps or immediately continues that period.

The implementation should be tested for subscription changes on the same date, gaps between subscriptions, reactivations, open-ended subscriptions, and future end dates.