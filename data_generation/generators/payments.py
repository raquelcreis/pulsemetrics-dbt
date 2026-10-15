from datetime import datetime, timedelta
import random

import pandas as pd


# ================================================================
# Reproducibility
# ================================================================

random.seed(42)


# ================================================================
# Configuration
# ================================================================

PLAN_PRICES = {
    "P001": 100.00,   # Starter
    "P002": 300.00,   # Growth
    "P003": 1000.00,  # Enterprise
    "P004": 400.00,   # Growth
    "P005": 1200.00,  # Enterprise
}


PAYMENT_STATUS_DISTRIBUTION = {
    "DIRECT_PAID": 0.88,
    "RETRY_PAID": 0.08,
    "FAILED": 0.04,
}


PAYMENT_METHOD_DISTRIBUTION = {
    "CREDIT_CARD": 0.65,
    "PIX": 0.25,
    "BANK_TRANSFER": 0.10,
}


REFUND_RATE = 0.01


CURRENCY = "USD"


PROJECT_START_DATE = pd.Timestamp("2025-01-01")
PROJECT_END_DATE = pd.Timestamp("2026-12-31")


# ================================================================
# Helper functions
# ================================================================

def get_month_starts(start_date, end_date):
    """
    Generate the first day of each month between two dates.
    """

    start_date = pd.Timestamp(start_date)
    end_date = pd.Timestamp(end_date)

    first_month = start_date.replace(day=1)
    last_month = end_date.replace(day=1)

    return pd.date_range(
        start=first_month,
        end=last_month,
        freq="MS",
    )


def choose_payment_method():
    """
    Choose a payment method based on the configured distribution.
    """

    return random.choices(
        population=list(PAYMENT_METHOD_DISTRIBUTION.keys()),
        weights=list(PAYMENT_METHOD_DISTRIBUTION.values()),
        k=1,
    )[0]


def choose_payment_scenario():
    """
    Decide how the billing period will behave.

    Possible scenarios:

    - DIRECT_PAID
    - RETRY_PAID
    - FAILED
    """

    return random.choices(
        population=list(PAYMENT_STATUS_DISTRIBUTION.keys()),
        weights=list(PAYMENT_STATUS_DISTRIBUTION.values()),
        k=1,
    )[0]


def generate_payment_datetime(billing_period_start):
    """
    Generate a payment timestamp inside the billing month.
    """

    billing_period_start = pd.Timestamp(
        billing_period_start
    )

    day = random.randint(1, 25)
    hour = random.randint(8, 20)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)

    return billing_period_start + pd.Timedelta(
        days=day - 1,
        hours=hour,
        minutes=minute,
        seconds=second,
    )


def generate_payment(
    payment_id,
    subscription_id,
    billing_period_start_date,
    amount,
    status,
    payment_method,
    payment_datetime,
):
    """
    Create one payment attempt.
    """

    created_at = payment_datetime + pd.Timedelta(
        seconds=random.randint(0, 30)
    )

    return {
        "payment_id": payment_id,
        "subscription_id": subscription_id,
        "billing_period_start_date": billing_period_start_date,
        "payment_datetime": payment_datetime,
        "amount": amount,
        "currency": CURRENCY,
        "status": status,
        "payment_method": payment_method,
        "created_at": created_at,
    }


# ================================================================
# Main generator
# ================================================================

def generate_payments(subscriptions):
    """
    Generate payment attempts for subscription billing periods.

    Important business rule:

    One subscription can have multiple payment attempts
    for the same billing period.

    Example:

        2026-03
        FAILED
        FAILED
        PAID

    The billing period itself is considered paid because
    at least one attempt was successful.

    The dbt layer will later aggregate these attempts into
    billing-period-level metrics.
    """

    payments = []
    payment_number = 1

    for _, subscription in subscriptions.iterrows():

        subscription_id = subscription["subscription_id"]
        plan_id = subscription["plan_id"]

        subscription_start = pd.Timestamp(
            subscription["start_date"]
        )

        subscription_end = subscription["end_date"]

        if pd.isna(subscription_end):
            subscription_end = PROJECT_END_DATE

        else:
            subscription_end = pd.Timestamp(subscription_end)

        monthly_price = PLAN_PRICES[plan_id]

        # --------------------------------------------------------
        # Billing periods
        # --------------------------------------------------------

        billing_periods = get_month_starts(
            start_date=subscription_start,
            end_date=subscription_end,
        )

        for billing_period_start in billing_periods:

            billing_period_start = pd.Timestamp(
                billing_period_start
            )

            # Do not create billing periods before the
            # subscription actually started.
            if billing_period_start < subscription_start.replace(
                day=1
            ):
                continue

            # Do not create a billing period after the
            # subscription ended.
            if billing_period_start >= subscription_end.replace(
                day=1
            ):
                continue

            scenario = choose_payment_scenario()

            # ====================================================
            # DIRECT PAID
            # ====================================================

            if scenario == "DIRECT_PAID":

                payment_datetime = generate_payment_datetime(
                    billing_period_start
                )

                payment_method = choose_payment_method()

                status = "PAID"

                payment = generate_payment(
                    payment_id=f"PAY{payment_number:07d}",
                    subscription_id=subscription_id,
                    billing_period_start_date=billing_period_start,
                    amount=monthly_price,
                    status=status,
                    payment_method=payment_method,
                    payment_datetime=payment_datetime,
                )

                payments.append(payment)
                payment_number += 1

            # ====================================================
            # RETRY → PAID
            # ====================================================

            elif scenario == "RETRY_PAID":

                number_of_failures = random.choice([1, 2])

                base_datetime = generate_payment_datetime(
                    billing_period_start
                )

                for retry_number in range(number_of_failures):

                    failed_datetime = (
                        base_datetime
                        + pd.Timedelta(
                            days=retry_number * 2
                        )
                    )

                    failed_payment = generate_payment(
                        payment_id=f"PAY{payment_number:07d}",
                        subscription_id=subscription_id,
                        billing_period_start_date=billing_period_start,
                        amount=monthly_price,
                        status="FAILED",
                        payment_method=choose_payment_method(),
                        payment_datetime=failed_datetime,
                    )

                    payments.append(failed_payment)
                    payment_number += 1

                successful_datetime = (
                    base_datetime
                    + pd.Timedelta(
                        days=number_of_failures * 2
                    )
                )

                successful_payment = generate_payment(
                    payment_id=f"PAY{payment_number:07d}",
                    subscription_id=subscription_id,
                    billing_period_start_date=billing_period_start,
                    amount=monthly_price,
                    status="PAID",
                    payment_method=choose_payment_method(),
                    payment_datetime=successful_datetime,
                )

                payments.append(successful_payment)
                payment_number += 1

            # ====================================================
            # FAILED
            # ====================================================

            elif scenario == "FAILED":

                number_of_failures = random.choice([1, 2])

                base_datetime = generate_payment_datetime(
                    billing_period_start
                )

                for retry_number in range(number_of_failures):

                    failed_datetime = (
                        base_datetime
                        + pd.Timedelta(
                            days=retry_number * 2
                        )
                    )

                    failed_payment = generate_payment(
                        payment_id=f"PAY{payment_number:07d}",
                        subscription_id=subscription_id,
                        billing_period_start_date=billing_period_start,
                        amount=monthly_price,
                        status="FAILED",
                        payment_method=choose_payment_method(),
                        payment_datetime=failed_datetime,
                    )

                    payments.append(failed_payment)
                    payment_number += 1

    # ============================================================
    # Create DataFrame
    # ============================================================

    payments_df = pd.DataFrame(payments)

    # ============================================================
    # Refunds
    # ============================================================

    if not payments_df.empty:

        paid_mask = payments_df["status"] == "PAID"

        paid_indexes = payments_df.index[paid_mask].tolist()

        number_of_refunds = int(
            len(paid_indexes) * REFUND_RATE
        )

        if number_of_refunds > 0:

            refund_indexes = random.sample(
                paid_indexes,
                number_of_refunds,
            )

            payments_df.loc[
                refund_indexes,
                "status"
            ] = "REFUNDED"

    return payments_df


# ================================================================
# Local validation
# ================================================================

if __name__ == "__main__":

    # Small mock dataset for local testing.
    subscriptions = pd.DataFrame(
        {
            "subscription_id": [
                "S00001",
                "S00002",
            ],
            "customer_id": [
                "C0001",
                "C0002",
            ],
            "plan_id": [
                "P001",
                "P002",
            ],
            "start_date": [
                pd.Timestamp("2025-01-15"),
                pd.Timestamp("2025-06-10"),
            ],
            "end_date": [
                pd.Timestamp("2025-06-20"),
                pd.NaT,
            ],
            "created_at": [
                pd.Timestamp("2025-01-15"),
                pd.Timestamp("2025-06-10"),
            ],
        }
    )

    payments = generate_payments(
        subscriptions
    )

    print("Shape:", payments.shape)

    print("\nPayment IDs duplicados:")
    print(
        payments["payment_id"].duplicated().sum()
    )

    print("\nStatus:")
    print(
        payments["status"].value_counts()
    )

    print("\nPayment methods:")
    print(
        payments["payment_method"].value_counts()
    )

    print("\nSubscriptions:")
    print(
        payments["subscription_id"].nunique()
    )

    print("\nBilling periods:")
    print(
        payments[
            [
                "subscription_id",
                "billing_period_start_date",
            ]
        ]
        .drop_duplicates()
        .shape[0]
    )

    print("\nTotal amount:")
    print(
        payments["amount"].sum()
    )