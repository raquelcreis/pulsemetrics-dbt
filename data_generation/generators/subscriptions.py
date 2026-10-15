from datetime import timedelta
import random

import pandas as pd


# Reproducibility
random.seed(42)


TRAJECTORY_DISTRIBUTION = {
    "STABLE": 0.50,
    "UPGRADE": 0.18,
    "DOWNGRADE": 0.08,
    "CHURN": 0.14,
    "CHURN_REACTIVATION": 0.10,
}


PLAN_HIERARCHY = {
    "P001": 1,  # Starter
    "P002": 2,  # Growth
    "P003": 3,  # Enterprise
    "P004": 2,  # Growth
    "P005": 3,  # Enterprise
}


PROJECT_END_DATE = pd.Timestamp("2026-12-31")


def choose_initial_plan():
    """
    Choose the first plan for a customer.

    Customers are more likely to start on lower-tier plans.
    """

    return random.choices(
        population=["P001", "P002", "P003"],
        weights=[0.60, 0.30, 0.10],
        k=1,
    )[0]


def choose_plan_for_change(current_plan, direction):
    """
    Choose a new plan for an upgrade or downgrade.

    The plan hierarchy is used instead of the plan ID itself,
    because P002/P004 are both Growth and P003/P005 are both
    Enterprise.
    """

    current_level = PLAN_HIERARCHY[current_plan]

    if direction == "UPGRADE":
        possible_plans = [
            plan_id
            for plan_id, level in PLAN_HIERARCHY.items()
            if level > current_level
        ]

    elif direction == "DOWNGRADE":
        possible_plans = [
            plan_id
            for plan_id, level in PLAN_HIERARCHY.items()
            if level < current_level
        ]

    else:
        return current_plan

    if not possible_plans:
        return current_plan

    return random.choice(possible_plans)


def generate_subscription_period(
    customer_id,
    subscription_id,
    plan_id,
    start_date,
    end_date,
):
    """
    Create one subscription record.
    """

    created_at = start_date - timedelta(
        days=random.randint(0, 3),
    )

    return {
        "subscription_id": subscription_id,
        "customer_id": customer_id,
        "plan_id": plan_id,
        "start_date": start_date,
        "end_date": end_date,
        "created_at": created_at,
    }


def random_date_between(start_date, end_date):
    """
    Generate a random date between two dates.

    Returns None if there is not enough time between the dates.
    """

    if start_date >= end_date:
        return None

    days_available = (end_date - start_date).days

    return start_date + timedelta(
        days=random.randint(1, days_available),
    )


def generate_subscriptions(customers):
    """
    Generate coherent subscription histories for customers.

    Possible customer trajectories:

    - STABLE
    - UPGRADE
    - DOWNGRADE
    - CHURN
    - CHURN_REACTIVATION

    A customer can have multiple subscriptions over time,
    but subscription periods never overlap.
    """

    subscriptions = []
    subscription_number = 1

    for _, customer in customers.iterrows():

        customer_id = customer["customer_id"]

        customer_created_at = pd.Timestamp(
            customer["created_at"]
        )

        first_start_date = customer_created_at.normalize()

        trajectory = random.choices(
            population=list(TRAJECTORY_DISTRIBUTION.keys()),
            weights=list(TRAJECTORY_DISTRIBUTION.values()),
            k=1,
        )[0]

        current_plan = choose_initial_plan()

        # =========================================================
        # STABLE
        # =========================================================

        if trajectory == "STABLE":

            subscription = generate_subscription_period(
                customer_id=customer_id,
                subscription_id=f"S{subscription_number:05d}",
                plan_id=current_plan,
                start_date=first_start_date,
                end_date=None,
            )

            subscriptions.append(subscription)
            subscription_number += 1

        # =========================================================
        # UPGRADE / DOWNGRADE
        # =========================================================

        elif trajectory in {"UPGRADE", "DOWNGRADE"}:

            latest_possible_change = (
                PROJECT_END_DATE - timedelta(days=30)
            )

            change_date = random_date_between(
                start_date=first_start_date + timedelta(days=60),
                end_date=latest_possible_change,
            )

            new_plan = choose_plan_for_change(
                current_plan=current_plan,
                direction=trajectory,
            )

            # If there isn't enough time for a plan change,
            # keep the customer on a single subscription.
            if change_date is None or new_plan == current_plan:

                subscription = generate_subscription_period(
                    customer_id=customer_id,
                    subscription_id=f"S{subscription_number:05d}",
                    plan_id=current_plan,
                    start_date=first_start_date,
                    end_date=None,
                )

                subscriptions.append(subscription)
                subscription_number += 1

            else:

                first_subscription = generate_subscription_period(
                    customer_id=customer_id,
                    subscription_id=f"S{subscription_number:05d}",
                    plan_id=current_plan,
                    start_date=first_start_date,
                    end_date=change_date,
                )

                subscriptions.append(first_subscription)
                subscription_number += 1

                second_subscription = generate_subscription_period(
                    customer_id=customer_id,
                    subscription_id=f"S{subscription_number:05d}",
                    plan_id=new_plan,
                    start_date=change_date,
                    end_date=None,
                )

                subscriptions.append(second_subscription)
                subscription_number += 1

        # =========================================================
        # CHURN
        # =========================================================

        elif trajectory == "CHURN":

            latest_possible_churn = (
                PROJECT_END_DATE - timedelta(days=1)
            )

            churn_date = random_date_between(
                start_date=first_start_date + timedelta(days=90),
                end_date=latest_possible_churn,
            )

            # If there isn't enough time to create a churn period,
            # keep the customer active.
            if churn_date is None:

                subscription = generate_subscription_period(
                    customer_id=customer_id,
                    subscription_id=f"S{subscription_number:05d}",
                    plan_id=current_plan,
                    start_date=first_start_date,
                    end_date=None,
                )

                subscriptions.append(subscription)
                subscription_number += 1

            else:

                subscription = generate_subscription_period(
                    customer_id=customer_id,
                    subscription_id=f"S{subscription_number:05d}",
                    plan_id=current_plan,
                    start_date=first_start_date,
                    end_date=churn_date,
                )

                subscriptions.append(subscription)
                subscription_number += 1

        # =========================================================
        # CHURN + REACTIVATION
        # =========================================================

        elif trajectory == "CHURN_REACTIVATION":

            latest_possible_churn = (
                PROJECT_END_DATE - timedelta(days=90)
            )

            churn_date = random_date_between(
                start_date=first_start_date + timedelta(days=90),
                end_date=latest_possible_churn,
            )

            # If there isn't enough time for churn + reactivation,
            # keep the customer on a single active subscription.
            if churn_date is None:

                subscription = generate_subscription_period(
                    customer_id=customer_id,
                    subscription_id=f"S{subscription_number:05d}",
                    plan_id=current_plan,
                    start_date=first_start_date,
                    end_date=None,
                )

                subscriptions.append(subscription)
                subscription_number += 1

            else:

                reactivation_gap = timedelta(
                    days=random.randint(30, 120)
                )

                reactivation_date = (
                    churn_date + reactivation_gap
                )

                # If the reactivation would happen after the
                # project ends, don't create the second period.
                if reactivation_date >= PROJECT_END_DATE:

                    subscription = generate_subscription_period(
                        customer_id=customer_id,
                        subscription_id=f"S{subscription_number:05d}",
                        plan_id=current_plan,
                        start_date=first_start_date,
                        end_date=churn_date,
                    )

                    subscriptions.append(subscription)
                    subscription_number += 1

                else:

                    first_subscription = (
                        generate_subscription_period(
                            customer_id=customer_id,
                            subscription_id=(
                                f"S{subscription_number:05d}"
                            ),
                            plan_id=current_plan,
                            start_date=first_start_date,
                            end_date=churn_date,
                        )
                    )

                    subscriptions.append(first_subscription)
                    subscription_number += 1

                    reactivated_plan = random.choice(
                        [
                            current_plan,
                            choose_initial_plan(),
                        ]
                    )

                    second_subscription = (
                        generate_subscription_period(
                            customer_id=customer_id,
                            subscription_id=(
                                f"S{subscription_number:05d}"
                            ),
                            plan_id=reactivated_plan,
                            start_date=reactivation_date,
                            end_date=None,
                        )
                    )

                    subscriptions.append(second_subscription)
                    subscription_number += 1

    return pd.DataFrame(subscriptions)


if __name__ == "__main__":

    # Local validation only.
    # The production pipeline will import
    # generate_subscriptions() directly.

    customers = pd.DataFrame(
        {
            "customer_id": ["C0001", "C0002", "C0003"],
            "created_at": [
                pd.Timestamp("2025-01-10"),
                pd.Timestamp("2025-05-15"),
                pd.Timestamp("2026-03-20"),
            ],
        }
    )

    subscriptions = generate_subscriptions(customers)

    print("Shape:", subscriptions.shape)

    print("\nSubscriptions:")
    print(subscriptions)

    print("\nDuplicated subscription IDs:")
    print(subscriptions["subscription_id"].duplicated().sum())

    print("\nSubscriptions per customer:")
    print(
        subscriptions.groupby("customer_id")
        .size()
        .sort_values(ascending=False)
    )