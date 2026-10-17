
import os
import json
from pathlib import Path
from uuid import uuid4

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

RAW_COLUMNS = {
    "CUSTOMERS": [
        "ID", "CUSTOMER_NAME", "DOCUMENT", "EMAIL", "COUNTRY", "CREATED_AT"
    ],
    "PLANS": ["PLAN_ID", "PLAN_NAME", "MONTHLY_PRICE", "BILLING_CYCLE"],
    "SUBSCRIPTIONS": [
        "SUBSCRIPTION_ID", "CUSTOMER_ID", "PLAN_ID", "START_DATE", "END_DATE", "CREATED_AT"
    ],
    "PAYMENTS": [
        "PAYMENT_ID", "SUBSCRIPTION_ID", "BILLING_PERIOD_START_DATE",
        "PAYMENT_DATETIME", "AMOUNT", "CURRENCY", "STATUS", "PAYMENT_METHOD", "CREATED_AT"
    ],
    "PRODUCT_EVENTS": [
        "EVENT_ID", "CUSTOMER_ID", "EVENT_TYPE", "EVENT_TIMESTAMP",
        "EVENT_PROPERTIES", "CREATED_AT"
    ],
}

# Mirrors NOT NULL columns in infrastructure/snowflake/06_create_raw_tables.sql.
REQUIRED_COLUMNS = {
    "CUSTOMERS": ["ID", "DOCUMENT", "EMAIL", "COUNTRY", "CREATED_AT"],
    "PLANS": RAW_COLUMNS["PLANS"],
    "SUBSCRIPTIONS": [
        "SUBSCRIPTION_ID", "CUSTOMER_ID", "PLAN_ID", "START_DATE", "CREATED_AT"
    ],
    "PAYMENTS": RAW_COLUMNS["PAYMENTS"],
    "PRODUCT_EVENTS": [
        "EVENT_ID", "CUSTOMER_ID", "EVENT_TYPE", "EVENT_TIMESTAMP", "CREATED_AT"
    ],
}


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



def read_csv_with_schema(
    filename, expected_columns, dtype=None, keep_default_na=True
):
    path = OUTPUT_DIR / filename
    dataframe = pd.read_csv(
        path, dtype=dtype, keep_default_na=keep_default_na
    )

    if set(dataframe.columns) != set(expected_columns):
        missing = sorted(set(expected_columns) - set(dataframe.columns))
        unexpected = sorted(set(dataframe.columns) - set(expected_columns))
        raise ValueError(
            f"{filename} has an invalid schema; "
            f"missing columns: {missing}; unexpected columns: {unexpected}"
        )

    if dataframe.empty:
        raise ValueError(f"{filename} contains no data rows")

    return dataframe[expected_columns]


def validate_required_values(table_name, dataframe):
    for column in REQUIRED_COLUMNS[table_name]:
        missing = dataframe[column].isna()
        blank_strings = dataframe[column].map(
            lambda value: isinstance(value, str) and not value.strip()
        )
        missing_count = int((missing | blank_strings).sum())
        if missing_count:
            raise ValueError(
                f"{table_name} contains {missing_count} missing value(s) "
                f"in required column {column}"
            )


def reject_nonstandard_json_constant(value):
    raise ValueError(f"Nonstandard JSON constant {value!r} is not allowed")


def prepare_input_data():
    """Read, validate, and normalize every input before connecting to Snowflake."""
    customers = read_csv_with_schema(
        "customers.csv",
        ["customer_id", "customer_name", "document", "email", "country", "created_at"],
    ).rename(columns={"customer_id": "id"})
    customers["created_at"] = pd.to_datetime(customers["created_at"], errors="raise")
    customers.columns = [column.upper() for column in customers.columns]

    plans = pd.DataFrame(
        PLANS,
        columns=[
            "PLAN_ID",
            "PLAN_NAME",
            "MONTHLY_PRICE",
            "BILLING_CYCLE",
        ],
    )

    subscriptions = read_csv_with_schema(
        "subscriptions.csv",
        ["subscription_id", "customer_id", "plan_id", "start_date", "end_date", "created_at"],
    )
    subscriptions["start_date"] = pd.to_datetime(
        subscriptions["start_date"], errors="raise"
    ).dt.date
    subscriptions["end_date"] = pd.to_datetime(
        subscriptions["end_date"], errors="raise"
    ).dt.date
    subscriptions["created_at"] = pd.to_datetime(
        subscriptions["created_at"], errors="raise"
    )
    subscriptions.columns = [column.upper() for column in subscriptions.columns]

    payments = read_csv_with_schema(
        "payments.csv",
        [
            "payment_id", "subscription_id", "billing_period_start_date",
            "payment_datetime", "amount", "currency", "status", "payment_method", "created_at"
        ],
    )
    payments["billing_period_start_date"] = pd.to_datetime(
        payments["billing_period_start_date"], errors="raise"
    ).dt.date
    for column in ["payment_datetime", "created_at"]:
        payments[column] = pd.to_datetime(payments[column], errors="raise")
    payments.columns = [column.upper() for column in payments.columns]

    product_events = read_csv_with_schema(
        "product_events.csv",
        [
            "event_id", "customer_id", "event_type", "event_timestamp",
            "event_properties", "created_at"
        ],
        dtype={"event_properties": str},
        keep_default_na=False,
    )
    for column in ["event_timestamp", "created_at"]:
        product_events[column] = pd.to_datetime(
            product_events[column], errors="raise"
        )
    for row_number, (index, properties) in enumerate(
        product_events["event_properties"].items(), start=2
    ):
        if not properties.strip():
            product_events.at[index, "event_properties"] = None
            continue

        try:
            json.loads(
                properties,
                parse_constant=reject_nonstandard_json_constant,
            )
        except ValueError as exc:
            raise ValueError(
                "PRODUCT_EVENTS has invalid JSON in EVENT_PROPERTIES "
                f"at CSV row {row_number}: {exc}"
            ) from exc
    product_events.columns = [column.upper() for column in product_events.columns]

    datasets = {
        "CUSTOMERS": customers,
        "PLANS": plans,
        "SUBSCRIPTIONS": subscriptions,
        "PAYMENTS": payments,
        "PRODUCT_EVENTS": product_events,
    }
    for table_name, dataframe in datasets.items():
        if dataframe.empty:
            raise ValueError(f"{table_name} input contains no data rows")
        if list(dataframe.columns) != RAW_COLUMNS[table_name]:
            raise ValueError(f"{table_name} does not match the RAW table schema")
        validate_required_values(table_name, dataframe)

    return datasets


def create_temporary_tables(conn):
    """Create isolated, session-scoped tables with the RAW table contracts."""
    suffix = uuid4().hex.upper()
    table_names = {
        table_name: f"_LOAD_{table_name}_{suffix}"
        for table_name in TABLES
    }

    with conn.cursor() as cursor:
        for table_name in TABLES:
            temporary_name = table_names[table_name]
            cursor.execute(
                f"CREATE TEMPORARY TABLE {DATABASE}.{SCHEMA}.{temporary_name} "
                f"LIKE {DATABASE}.{SCHEMA}.{table_name}"
            )

    return table_names


def load_product_events(conn, dataframe, table_name):
    total_rows = 0
    batch_size = 500

    insert_prefix = """
        INSERT INTO {DATABASE}.{SCHEMA}.{table_name} (
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

    for start in range(0, len(dataframe), 2000):
        df = dataframe.iloc[start:start + 2000]
        records = []

        for row in df.itertuples(index=False, name=None):
            event_id, customer_id, event_type, event_timestamp, properties, created_at = row

            if pd.isna(properties):
                properties = None

            records.append(
                (
                    event_id,
                    customer_id,
                    event_type,
                    pd.Timestamp(event_timestamp).to_pydatetime(),
                    properties,
                    pd.Timestamp(created_at).to_pydatetime(),
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

            sql = insert_prefix.format(
                DATABASE=DATABASE, SCHEMA=SCHEMA, table_name=table_name
            ) + placeholders

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



def validate_counts(conn, table_names, expected_counts):
    print("\nValidating row counts...")

    for table_name in TABLES:
        temporary_name = table_names[table_name]
        with conn.cursor() as cursor:
            cursor.execute(
                f"SELECT COUNT(*) "
                f"FROM {DATABASE}.{SCHEMA}.{temporary_name}"
            )
            actual = cursor.fetchone()[0]

        expected_count = expected_counts[table_name]
        if actual != expected_count:
            raise RuntimeError(
                f"{table_name}: expected "
                f"{expected_count:,}, got {actual:,}"
            )

        print(
            f"  {table_name}: {actual:,} rows"
        )


def load_temporary_tables(conn, datasets, table_names):
    for table_name in TABLES:
        dataframe = datasets[table_name]
        temporary_name = table_names[table_name]

        if table_name == "PRODUCT_EVENTS":
            load_product_events(conn, dataframe, temporary_name)
        else:
            load_with_write_pandas(conn, dataframe, temporary_name)


def replace_raw_tables_atomically(conn, table_names):
    """Replace all production rows in one explicit Snowflake DML transaction."""
    cursor = conn.cursor()
    try:
        cursor.execute("BEGIN TRANSACTION")

        for table_name in reversed(TABLES):
            cursor.execute(
                f"DELETE FROM {DATABASE}.{SCHEMA}.{table_name}"
            )

        for table_name in TABLES:
            columns = ", ".join(RAW_COLUMNS[table_name])
            temporary_name = table_names[table_name]
            cursor.execute(
                f"INSERT INTO {DATABASE}.{SCHEMA}.{table_name} ({columns}) "
                f"SELECT {columns} FROM {DATABASE}.{SCHEMA}.{temporary_name}"
            )

        cursor.execute("COMMIT")
    except Exception:
        try:
            cursor.execute("ROLLBACK")
        except Exception:
            # Preserve the load error; Snowflake rolls back any open transaction
            # when the session is closed.
            pass
        raise
    finally:
        cursor.close()


def main():
    print("=" * 60)
    print("PulseMetrics - Load RAW tables")
    print("=" * 60)

    # Fail before any warehouse work if a file, schema, date, or JSON value is invalid.
    datasets = prepare_input_data()
    expected_counts = {
        table_name: len(dataframe)
        for table_name, dataframe in datasets.items()
    }

    conn = connect_to_snowflake()

    try:
        print("\nCreating temporary replacement tables...")
        temporary_tables = create_temporary_tables(conn)

        print("\nLoading temporary datasets...")
        load_temporary_tables(conn, datasets, temporary_tables)
        validate_counts(conn, temporary_tables, expected_counts)

        print("\nReplacing RAW data in one transaction...")
        replace_raw_tables_atomically(conn, temporary_tables)

        print("\nRAW loading completed successfully!")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
