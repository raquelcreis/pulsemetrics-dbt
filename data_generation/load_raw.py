
import os
import json
from pathlib import Path

import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
PRIVATE_KEY_PATH = PROJECT_ROOT / ".secrets" / "rsa_key.p8"

ACCOUNT = "ELJCPIJ-OO28101"
USER = "PULSEMETRICS_DBT_USER"
ROLE = "PULSEMETRICS_INGEST"
WAREHOUSE = "PULSEMETRICS_WH"
DATABASE = "PULSEMETRICS"
SCHEMA = "RAW"

PLANS = [
    ("P001", "Starter", 100.00, "MONTHLY"),
    ("P002", "Growth", 300.00, "MONTHLY"),
    ("P003", "Enterprise", 1000.00, "MONTHLY"),
    ("P004", "Growth", 400.00, "MONTHLY"),
    ("P005", "Enterprise", 1200.00, "MONTHLY"),
]

# Keep insertion order aligned with the RAW table contracts.
TABLES = [
    "CUSTOMERS",
    "PLANS",
    "SUBSCRIPTIONS",
    "PAYMENTS",
    "PRODUCT_EVENTS",
]


def connect_to_snowflake():
    passphrase = os.getenv(
        "DBT_SNOWFLAKE_PRIVATE_KEY_PASSPHRASE"
    )

    if not passphrase:
        raise RuntimeError(
            "Environment variable "
            "DBT_SNOWFLAKE_PRIVATE_KEY_PASSPHRASE "
            "is not set."
        )

    if not PRIVATE_KEY_PATH.exists():
        raise FileNotFoundError(
            f"Private key not found: {PRIVATE_KEY_PATH}"
        )

    return snowflake.connector.connect(
        account=ACCOUNT,
        user=USER,
        private_key_file=str(PRIVATE_KEY_PATH),
        private_key_file_pwd=passphrase,
        role=ROLE,
        warehouse=WAREHOUSE,
        database=DATABASE,
        schema=SCHEMA,
    )



def load_with_write_pandas(conn, dataframe, table_name):
    success, chunks, rows, output = write_pandas(
        conn=conn,
        df=dataframe,
        table_name=table_name,
        database=DATABASE,
        schema=SCHEMA,
        auto_create_table=False,
        overwrite=False,
        quote_identifiers=False,
        use_logical_type=True,
    )

    if not success:
        raise RuntimeError(
            f"Failed loading {table_name}: {output}"
        )

    print(
        f"  {table_name}: {rows:,} rows loaded "
        f"across {chunks} chunk(s)"
    )



def load_customers(conn):
    df = pd.read_csv(OUTPUT_DIR / "customers.csv")

    # The RAW contract uses `id`, while the generator
    # names this field `customer_id`.
    df = df.rename(
        columns={"customer_id": "id"}
    )

    df["created_at"] = pd.to_datetime(
        df["created_at"]
    )

    df.columns = [
        column.upper()
        for column in df.columns
    ]

    load_with_write_pandas(
        conn,
        df,
        "CUSTOMERS",
    )


def load_plans(conn):
    df = pd.DataFrame(
        PLANS,
        columns=[
            "PLAN_ID",
            "PLAN_NAME",
            "MONTHLY_PRICE",
            "BILLING_CYCLE",
        ],
    )

    load_with_write_pandas(
        conn,
        df,
        "PLANS",
    )


def load_subscriptions(conn):
    df = pd.read_csv(
        OUTPUT_DIR / "subscriptions.csv"
    )

    df["start_date"] = pd.to_datetime(
        df["start_date"]
    ).dt.date

    df["end_date"] = pd.to_datetime(
        df["end_date"],
        errors="coerce",
    ).dt.date

    df["created_at"] = pd.to_datetime(
        df["created_at"]
    )

    df.columns = [
        column.upper()
        for column in df.columns
    ]

    load_with_write_pandas(
        conn,
        df,
        "SUBSCRIPTIONS",
    )


def load_payments(conn):
    df = pd.read_csv(
        OUTPUT_DIR / "payments.csv"
    )

    df["billing_period_start_date"] = pd.to_datetime(
        df["billing_period_start_date"]
    ).dt.date

    df["payment_datetime"] = pd.to_datetime(
        df["payment_datetime"]
    )

    df["created_at"] = pd.to_datetime(
        df["created_at"]
    )

    df.columns = [
        column.upper()
        for column in df.columns
    ]

    load_with_write_pandas(
        conn,
        df,
        "PAYMENTS",
    )



def load_product_events(conn):
    csv_path = OUTPUT_DIR / "product_events.csv"
    total_rows = 0
    batch_size = 500

    insert_prefix = """
        INSERT INTO PULSEMETRICS.RAW.PRODUCT_EVENTS (
            EVENT_ID,
            CUSTOMER_ID,
            EVENT_TYPE,
            EVENT_TIMESTAMP,
            EVENT_PROPERTIES,
            CREATED_AT
        )
        SELECT
            column1,
            column2,
            column3,
            column4,
            PARSE_JSON(column5),
            column6
        FROM VALUES
    """

    for df in pd.read_csv(
        csv_path,
        chunksize=2000,
        dtype={"event_properties": str},
    ):
        records = []

        for row in df.itertuples(index=False):
            properties = row.event_properties

            if pd.isna(properties):
                properties = None
            else:
                # Validate the JSON before sending it to Snowflake.
                json.loads(properties)

            records.append(
                (
                    row.event_id,
                    row.customer_id,
                    row.event_type,
                    pd.Timestamp(
                        row.event_timestamp
                    ).to_pydatetime(),
                    properties,
                    pd.Timestamp(
                        row.created_at
                    ).to_pydatetime(),
                )
            )

        # Insert smaller batches using a VALUES clause.
        # This avoids executemany's multi-row rewrite issue.
        for start in range(0, len(records), batch_size):
            batch = records[start:start + batch_size]

            placeholders = ", ".join(
                ["(%s, %s, %s, %s, %s, %s)"]
                * len(batch)
            )

            sql = insert_prefix + placeholders

            params = [
                value
                for record in batch
                for value in record
            ]

            with conn.cursor() as cursor:
                cursor.execute(sql, params)

            total_rows += len(batch)

        if total_rows and total_rows % 20000 < len(records):
            print(
                f"  PRODUCT_EVENTS: "
                f"{total_rows:,} rows inserted"
            )

    print(
        f"  PRODUCT_EVENTS: {total_rows:,} rows loaded"
    )



def validate_counts(conn):
    print("\nValidating row counts...")

    expected = {
        "CUSTOMERS": 1000,
        "PLANS": len(PLANS),
        "SUBSCRIPTIONS": None,
        "PAYMENTS": None,
        "PRODUCT_EVENTS": None,
    }

    for table_name in TABLES:
        with conn.cursor() as cursor:
            cursor.execute(
                f"SELECT COUNT(*) "
                f"FROM {DATABASE}.{SCHEMA}.{table_name}"
            )
            actual = cursor.fetchone()[0]

        expected_count = expected[table_name]

        if (
            expected_count is not None
            and actual != expected_count
        ):
            raise RuntimeError(
                f"{table_name}: expected "
                f"{expected_count:,}, got {actual:,}"
            )

        print(
            f"  {table_name}: {actual:,} rows"
        )


def main():
    if not OUTPUT_DIR.exists():
        raise FileNotFoundError(
            f"CSV directory not found: {OUTPUT_DIR}"
        )

    print("=" * 60)
    print("PulseMetrics - Load RAW tables")
    print("=" * 60)

    conn = connect_to_snowflake()

    try:
        # Clear existing data so rerunning a successful
        # load does not duplicate rows.
        print("\nClearing existing RAW data...")

        with conn.cursor() as cursor:
            for table_name in reversed(TABLES):
                cursor.execute(
                    f"DELETE FROM "
                    f"{DATABASE}.{SCHEMA}.{table_name}"
                )

        conn.commit()

        print("\nLoading datasets...")

        load_customers(conn)
        load_plans(conn)
        load_subscriptions(conn)
        load_payments(conn)
        load_product_events(conn)

        conn.commit()

        validate_counts(conn)

        print("\nRAW loading completed successfully!")

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    main()
