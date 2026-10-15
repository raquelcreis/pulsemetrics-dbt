import json
from pathlib import Path

from generators.customers import generate_customers
from generators.subscriptions import generate_subscriptions
from generators.payments import generate_payments
from generators.product_events import generate_product_events


# ================================================================
# Configuration
# ================================================================

OUTPUT_DIR = Path(__file__).parent / "output"


# ================================================================
# Main pipeline
# ================================================================

def main():

    print("=" * 60)
    print("PulseMetrics - Synthetic Data Generation")
    print("=" * 60)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ------------------------------------------------------------
    # 1. Customers
    # ------------------------------------------------------------

    print("\n[1/4] Generating customers...")

    customers = generate_customers()

    print(
        f"Customers generated: {len(customers):,}"
    )

    # ------------------------------------------------------------
    # 2. Subscriptions
    # ------------------------------------------------------------

    print("\n[2/4] Generating subscriptions...")

    subscriptions = generate_subscriptions(
        customers
    )

    print(
        f"Subscriptions generated: "
        f"{len(subscriptions):,}"
    )

    # ------------------------------------------------------------
    # 3. Payments
    # ------------------------------------------------------------

    print("\n[3/4] Generating payments...")

    payments = generate_payments(
        subscriptions
    )

    print(
        f"Payments generated: "
        f"{len(payments):,}"
    )

    # ------------------------------------------------------------
    # 4. Product events
    # ------------------------------------------------------------

    print("\n[4/4] Generating product events...")

    product_events = generate_product_events(
        customers=customers,
        subscriptions=subscriptions,
    )

    print(
        f"Product events generated: "
        f"{len(product_events):,}"
    )

    # ============================================================
    # Save datasets
    # ============================================================

    datasets = {
        "customers": customers,
        "subscriptions": subscriptions,
        "payments": payments,
        "product_events": product_events,
    }

    print("\nSaving datasets...")

    for name, dataframe in datasets.items():

        output_path = OUTPUT_DIR / f"{name}.csv"

        dataframe_to_save = dataframe.copy()

        # Snowflake VARIANT expects valid JSON.
        # Convert Python dictionaries to JSON strings
        # before writing the CSV.
        if name == "product_events":

            dataframe_to_save["event_properties"] = (
                dataframe_to_save["event_properties"]
                .apply(json.dumps)
            )

        dataframe_to_save.to_csv(
            output_path,
            index=False,
        )

        print(
            f"  ✓ {output_path}"
        )

    # ============================================================
    # Summary
    # ============================================================

    print("\n" + "=" * 60)
    print("Generation completed successfully!")
    print("=" * 60)

    print("\nDataset summary:")

    for name, dataframe in datasets.items():

        print(
            f"  {name:20s} "
            f"{len(dataframe):>10,} rows"
        )


if __name__ == "__main__":
    main()