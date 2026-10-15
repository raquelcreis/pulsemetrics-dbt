from datetime import timedelta
import random

import pandas as pd


# ================================================================
# Reproducibility
# ================================================================

random.seed(42)


# ================================================================
# Configuration
# ================================================================

PROJECT_START_DATE = pd.Timestamp("2025-01-01")
PROJECT_END_DATE = pd.Timestamp("2026-12-31")


# Expected weekly activity by latent engagement level.
#
# These values are not stored in RAW.
# They are only used to generate realistic behavior.
ENGAGEMENT_DISTRIBUTION = {
    "HIGH": {
        "min_events_per_week": 8,
        "max_events_per_week": 15,
    },
    "MEDIUM": {
        "min_events_per_week": 3,
        "max_events_per_week": 7,
    },
    "LOW": {
        "min_events_per_week": 0,
        "max_events_per_week": 2,
    },
}


# Event probabilities by engagement level.
#
# More engaged customers are more likely to use deeper product
# functionality rather than only logging in.
EVENT_DISTRIBUTION = {
    "HIGH": {
        "LOGIN": 0.25,
        "DASHBOARD_VIEWED": 0.25,
        "REPORT_CREATED": 0.18,
        "REPORT_EXPORTED": 0.12,
        "INTEGRATION_CONNECTED": 0.10,
        "TEAM_MEMBER_ADDED": 0.10,
    },
    "MEDIUM": {
        "LOGIN": 0.35,
        "DASHBOARD_VIEWED": 0.32,
        "REPORT_CREATED": 0.14,
        "REPORT_EXPORTED": 0.08,
        "INTEGRATION_CONNECTED": 0.06,
        "TEAM_MEMBER_ADDED": 0.05,
    },
    "LOW": {
        "LOGIN": 0.55,
        "DASHBOARD_VIEWED": 0.35,
        "REPORT_CREATED": 0.05,
        "REPORT_EXPORTED": 0.03,
        "INTEGRATION_CONNECTED": 0.01,
        "TEAM_MEMBER_ADDED": 0.01,
    },
}


# Enterprise customers have a higher probability of deeper
# product actions, but engagement still remains the main driver.
ENTERPRISE_DEEP_ACTION_BOOST = 1.20


# Probability of a customer changing their engagement level
# during a month.
ENGAGEMENT_CHANGE_PROBABILITY = 0.08


# Probability of a significant activity decline before churn.
PRE_CHURN_DECLINE_PROBABILITY = 0.75


# ================================================================
# Helper functions
# ================================================================

def choose_initial_engagement():
    """
    Assign a latent engagement level to a customer.

    This attribute is intentionally NOT stored in RAW.

    It exists only as a hidden variable used to generate
    correlated product behavior.
    """

    return random.choices(
        population=["HIGH", "MEDIUM", "LOW"],
        weights=[0.30, 0.50, 0.20],
        k=1,
    )[0]


def choose_next_engagement(current_engagement):
    """
    Occasionally change a customer's engagement level.

    Customers are more likely to remain at the same level than
    to change behavior dramatically.
    """

    if random.random() > ENGAGEMENT_CHANGE_PROBABILITY:
        return current_engagement

    transitions = {
        "HIGH": ["HIGH", "MEDIUM"],
        "MEDIUM": ["HIGH", "MEDIUM", "LOW"],
        "LOW": ["MEDIUM", "LOW"],
    }

    weights = {
        "HIGH": [0.70, 0.30],
        "MEDIUM": [0.20, 0.60, 0.20],
        "LOW": [0.30, 0.70],
    }

    possible_levels = transitions[current_engagement]
    possible_weights = weights[current_engagement]

    return random.choices(
        population=possible_levels,
        weights=possible_weights,
        k=1,
    )[0]


def get_subscription_status(
    event_date,
    subscription_start,
    subscription_end,
):
    """
    Determine whether a date falls inside a subscription period.
    """

    if event_date < subscription_start:
        return False

    if subscription_end is not None:
        if event_date >= subscription_end:
            return False

    return True


def get_weekly_event_count(engagement_level):
    """
    Generate the number of events for one customer-week.
    """

    config = ENGAGEMENT_DISTRIBUTION[engagement_level]

    return random.randint(
        config["min_events_per_week"],
        config["max_events_per_week"],
    )


def choose_event_type(
    engagement_level,
    plan_id,
):
    """
    Choose an event type based on engagement level.

    Enterprise customers receive a slight boost toward
    deeper product actions.
    """

    distribution = EVENT_DISTRIBUTION[
        engagement_level
    ].copy()

    enterprise_plans = {
        "P003",
        "P005",
    }

    if plan_id in enterprise_plans:

        deep_actions = {
            "REPORT_CREATED",
            "REPORT_EXPORTED",
            "INTEGRATION_CONNECTED",
            "TEAM_MEMBER_ADDED",
        }

        for event_type in deep_actions:
            distribution[event_type] *= (
                ENTERPRISE_DEEP_ACTION_BOOST
            )

    event_types = list(distribution.keys())
    weights = list(distribution.values())

    return random.choices(
        population=event_types,
        weights=weights,
        k=1,
    )[0]


def generate_event_properties(event_type):
    """
    Generate a small JSON-like dictionary of properties.

    These properties will eventually be stored in Snowflake
    as VARIANT.
    """

    if event_type == "LOGIN":

        return {
            "device": random.choice(
                [
                    "desktop",
                    "mobile",
                    "tablet",
                ]
            )
        }

    if event_type == "DASHBOARD_VIEWED":

        return {
            "dashboard": random.choice(
                [
                    "overview",
                    "financial",
                    "sales",
                    "operations",
                ]
            )
        }

    if event_type == "REPORT_CREATED":

        return {
            "report_type": random.choice(
                [
                    "financial",
                    "sales",
                    "operations",
                    "customer",
                ]
            )
        }

    if event_type == "REPORT_EXPORTED":

        return {
            "report_type": random.choice(
                [
                    "financial",
                    "sales",
                    "operations",
                    "customer",
                ]
            ),
            "export_format": random.choice(
                [
                    "csv",
                    "xlsx",
                    "pdf",
                ]
            ),
        }

    if event_type == "INTEGRATION_CONNECTED":

        return {
            "integration": random.choice(
                [
                    "salesforce",
                    "hubspot",
                    "slack",
                    "google_ads",
                ]
            )
        }

    if event_type == "TEAM_MEMBER_ADDED":

        return {
            "role": random.choice(
                [
                    "analyst",
                    "manager",
                    "admin",
                    "viewer",
                ]
            )
        }

    return {}


def generate_event_timestamp(
    week_start,
):
    """
    Generate a random timestamp inside a given week.
    """

    day_offset = random.randint(0, 6)

    hour = random.randint(8, 20)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)

    return (
        week_start
        + timedelta(days=day_offset)
        + timedelta(
            hours=hour,
            minutes=minute,
            seconds=second,
        )
    )


def get_week_starts(
    start_date,
    end_date,
):
    """
    Generate weekly periods between two dates.
    """

    start_date = pd.Timestamp(start_date)
    end_date = pd.Timestamp(end_date)

    first_week = start_date - pd.Timedelta(
        days=start_date.weekday()
    )

    last_week = end_date - pd.Timedelta(
        days=end_date.weekday()
    )

    return pd.date_range(
        start=first_week,
        end=last_week,
        freq="7D",
    )


def calculate_activity_multiplier(
    week_start,
    subscription_start,
    subscription_end,
):
    """
    Calculate a lifecycle-based activity multiplier.

    General behavior:

    - Early lifecycle: normal activity
    - Long-running subscription: normal activity
    - Pre-churn period: activity may decline significantly

    This creates a relationship between product activity
    and churn without making the relationship deterministic.
    """

    multiplier = 1.0

    subscription_start = pd.Timestamp(
        subscription_start
    )

    # ------------------------------------------------------------
    # New customer effect
    # ------------------------------------------------------------

    days_since_start = (
        week_start - subscription_start
    ).days

    if 0 <= days_since_start <= 30:

        # New customers are slightly more active while
        # exploring the product.
        multiplier *= random.uniform(
            1.05,
            1.35,
        )

    # ------------------------------------------------------------
    # Pre-churn effect
    # ------------------------------------------------------------

    if subscription_end is not None:

        subscription_end = pd.Timestamp(
            subscription_end
        )

        days_until_end = (
            subscription_end - week_start
        ).days

        if (
            0 <= days_until_end <= 45
            and random.random()
            < PRE_CHURN_DECLINE_PROBABILITY
        ):

            multiplier *= random.uniform(
                0.25,
                0.65,
            )

    return multiplier


# ================================================================
# Main generator
# ================================================================

def generate_product_events(
    customers,
    subscriptions,
):
    """
    Generate product events for customers based on their
    subscription lifecycle and latent engagement.

    The generator intentionally creates correlated behavior:

        engagement
            ↓
        event frequency
            ↓
        product activity
            ↓
        potential relationship with churn / upgrade

    The latent engagement variable is NOT stored in RAW.
    """

    events = []
    event_number = 1

    # ------------------------------------------------------------
    # Build subscription lookup
    # ------------------------------------------------------------

    subscriptions_by_customer = {}

    for _, subscription in subscriptions.iterrows():

        customer_id = subscription["customer_id"]

        if customer_id not in subscriptions_by_customer:
            subscriptions_by_customer[customer_id] = []

        subscriptions_by_customer[
            customer_id
        ].append(subscription)

    # ------------------------------------------------------------
    # Generate events customer by customer
    # ------------------------------------------------------------

    for _, customer in customers.iterrows():

        customer_id = customer["customer_id"]

        customer_created_at = pd.Timestamp(
            customer["created_at"]
        )

        customer_subscriptions = (
            subscriptions_by_customer.get(
                customer_id,
                [],
            )
        )

        if not customer_subscriptions:
            continue

        # --------------------------------------------------------
        # Latent engagement
        # --------------------------------------------------------

        engagement_level = (
            choose_initial_engagement()
        )

        # --------------------------------------------------------
        # Generate weekly activity
        # --------------------------------------------------------

        for subscription in customer_subscriptions:

            subscription_start = pd.Timestamp(
                subscription["start_date"]
            )

            subscription_end = subscription["end_date"]

            if pd.isna(subscription_end):
                subscription_end = None

            else:
                subscription_end = pd.Timestamp(
                    subscription_end
                )

            plan_id = subscription["plan_id"]

            lifecycle_start = max(
                subscription_start,
                customer_created_at.normalize(),
                PROJECT_START_DATE,
            )

            lifecycle_end = PROJECT_END_DATE

            if subscription_end is not None:

                lifecycle_end = min(
                    lifecycle_end,
                    subscription_end
                    - pd.Timedelta(days=1),
                )

            if lifecycle_start > lifecycle_end:
                continue

            week_starts = get_week_starts(
                lifecycle_start,
                lifecycle_end,
            )

            for week_start in week_starts:

                # ------------------------------------------------
                # Update engagement occasionally
                # ------------------------------------------------

                engagement_level = (
                    choose_next_engagement(
                        engagement_level
                    )
                )

                # ------------------------------------------------
                # Base weekly event count
                # ------------------------------------------------

                event_count = (
                    get_weekly_event_count(
                        engagement_level
                    )
                )

                # ------------------------------------------------
                # Lifecycle multiplier
                # ------------------------------------------------

                activity_multiplier = (
                    calculate_activity_multiplier(
                        week_start=week_start,
                        subscription_start=subscription_start,
                        subscription_end=subscription_end,
                    )
                )

                event_count = int(
                    round(
                        event_count
                        * activity_multiplier
                    )
                )

                # ------------------------------------------------
                # Prevent negative event counts
                # ------------------------------------------------

                event_count = max(
                    0,
                    event_count,
                )

                # ------------------------------------------------
                # Generate individual events
                # ------------------------------------------------

                for _ in range(event_count):

                    event_timestamp = (
                        generate_event_timestamp(
                            week_start
                        )
                    )

                    # Make sure the event is inside the
                    # subscription lifecycle.
                    if not get_subscription_status(
                        event_date=event_timestamp,
                        subscription_start=subscription_start,
                        subscription_end=subscription_end,
                    ):
                        continue

                    # Make sure the event is not before
                    # the global project start.
                    if (
                        event_timestamp
                        < PROJECT_START_DATE
                    ):
                        continue

                    # Make sure the event is not after
                    # the global project end.
                    if (
                        event_timestamp
                        > PROJECT_END_DATE
                    ):
                        continue

                    event_type = choose_event_type(
                        engagement_level=engagement_level,
                        plan_id=plan_id,
                    )

                    event_properties = (
                        generate_event_properties(
                            event_type
                        )
                    )

                    created_at = (
                        event_timestamp
                        + pd.Timedelta(
                            seconds=random.randint(
                                0,
                                30,
                            )
                        )
                    )

                    event = {
                        "event_id": (
                            f"EVT{event_number:08d}"
                        ),
                        "customer_id": customer_id,
                        "event_type": event_type,
                        "event_timestamp": (
                            event_timestamp
                        ),
                        "event_properties": (
                            event_properties
                        ),
                        "created_at": created_at,
                    }

                    events.append(event)

                    event_number += 1

    # ------------------------------------------------------------
    # Create DataFrame
    # ------------------------------------------------------------

    events_df = pd.DataFrame(events)

    return events_df


# ================================================================
# Local validation
# ================================================================

if __name__ == "__main__":

    # Small mock dataset for local testing.

    customers = pd.DataFrame(
        {
            "customer_id": [
                "C0001",
                "C0002",
                "C0003",
            ],
            "created_at": [
                pd.Timestamp("2025-01-10"),
                pd.Timestamp("2025-03-15"),
                pd.Timestamp("2025-06-20"),
            ],
        }
    )

    subscriptions = pd.DataFrame(
        {
            "subscription_id": [
                "S00001",
                "S00002",
                "S00003",
                "S00004",
            ],
            "customer_id": [
                "C0001",
                "C0002",
                "C0002",
                "C0003",
            ],
            "plan_id": [
                "P001",
                "P002",
                "P003",
                "P005",
            ],
            "start_date": [
                pd.Timestamp("2025-01-10"),
                pd.Timestamp("2025-03-15"),
                pd.Timestamp("2025-09-01"),
                pd.Timestamp("2025-06-20"),
            ],
            "end_date": [
                pd.Timestamp("2025-08-01"),
                pd.Timestamp("2025-08-31"),
                pd.NaT,
                pd.NaT,
            ],
            "created_at": [
                pd.Timestamp("2025-01-10"),
                pd.Timestamp("2025-03-15"),
                pd.Timestamp("2025-09-01"),
                pd.Timestamp("2025-06-20"),
            ],
        }
    )

    events = generate_product_events(
        customers=customers,
        subscriptions=subscriptions,
    )

    print("Shape:", events.shape)

    print("\nEvent IDs duplicados:")
    print(
        events["event_id"].duplicated().sum()
    )

    print("\nCustomers:")
    print(
        events["customer_id"].nunique()
    )

    print("\nEvent types:")
    print(
        events["event_type"].value_counts()
    )

    print("\nDate range:")
    print(
        events["event_timestamp"].min(),
        "->",
        events["event_timestamp"].max(),
    )

    print("\nNull customer IDs:")
    print(
        events["customer_id"].isna().sum()
    )

    print("\nNull event types:")
    print(
        events["event_type"].isna().sum()
    )

    print("\nExample event properties:")
    print(
        events[
            [
                "event_type",
                "event_properties",
            ]
        ].head(10)
    )