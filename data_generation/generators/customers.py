from datetime import datetime
import random

import pandas as pd
from faker import Faker


# Reproducibility
random.seed(42)
Faker.seed(42)

fake = Faker("pt_BR")


N_CUSTOMERS = 1_000

COUNTRY_DISTRIBUTION = {
    "BR": 0.55,
    "MX": 0.15,
    "AR": 0.10,
    "CL": 0.08,
    "CO": 0.07,
    "PE": 0.05,
}

START_DATE = datetime(2025, 1, 1)
END_DATE = datetime(2026, 12, 31)

PERIOD_DISTRIBUTION = {
    "2025_H1": 0.15,
    "2025_H2": 0.25,
    "2026_H1": 0.30,
    "2026_H2": 0.30,
}

PERIOD_RANGES = {
    "2025_H1": (
        datetime(2025, 1, 1),
        datetime(2025, 6, 30),
    ),
    "2025_H2": (
        datetime(2025, 7, 1),
        datetime(2025, 12, 31),
    ),
    "2026_H1": (
        datetime(2026, 1, 1),
        datetime(2026, 6, 30),
    ),
    "2026_H2": (
        datetime(2026, 7, 1),
        datetime(2026, 12, 31),
    ),
}


def generate_customers():
    customers = []

    for i in range(1, N_CUSTOMERS + 1):

        # Choose the period in which the customer joined
        period = random.choices(
            population=list(PERIOD_DISTRIBUTION.keys()),
            weights=list(PERIOD_DISTRIBUTION.values()),
            k=1,
        )[0]

        period_start, period_end = PERIOD_RANGES[period]

        # Generate a timestamp inside the selected period
        created_at = fake.date_time_between(
            start_date=period_start,
            end_date=period_end,
        )

        customer = {
            "customer_id": f"C{i:04d}",
            "customer_name": fake.company(),
            "document": fake.unique.cnpj(),
            "email": fake.unique.company_email(),
            "country": random.choices(
                population=list(COUNTRY_DISTRIBUTION.keys()),
                weights=list(COUNTRY_DISTRIBUTION.values()),
                k=1,
            )[0],
            "created_at": created_at,
        }

        customers.append(customer)

    return pd.DataFrame(customers)