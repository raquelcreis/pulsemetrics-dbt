import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd

from data_generation import load_raw


def write_valid_inputs(directory):
    datasets = {
        "customers": pd.DataFrame(
            [{
                "customer_id": "C0001",
                "customer_name": "Example Co",
                "document": "DOC1",
                "email": "example@example.com",
                "country": "BR",
                "created_at": "2025-01-01 12:00:00",
            }]
        ),
        "subscriptions": pd.DataFrame(
            [{
                "subscription_id": "S00001",
                "customer_id": "C0001",
                "plan_id": "P001",
                "start_date": "2025-01-01",
                "end_date": None,
                "created_at": "2025-01-01 12:00:00",
            }]
        ),
        "payments": pd.DataFrame(
            [{
                "payment_id": "PAY001",
                "subscription_id": "S00001",
                "billing_period_start_date": "2025-01-01",
                "payment_datetime": "2025-01-02 12:00:00",
                "amount": 100.00,
                "currency": "USD",
                "status": "PAID",
                "payment_method": "CREDIT_CARD",
                "created_at": "2025-01-02 12:00:00",
            }]
        ),
        "product_events": pd.DataFrame(
            [{
                "event_id": "E00001",
                "customer_id": "C0001",
                "event_type": "LOGIN",
                "event_timestamp": "2025-01-03 12:00:00",
                "event_properties": '{"source": "test"}',
                "created_at": "2025-01-03 12:00:00",
            }]
        ),
    }
    for name, dataframe in datasets.items():
        dataframe.to_csv(Path(directory) / f"{name}.csv", index=False)
    return datasets


class LoadRawSafetyTests(unittest.TestCase):
    def test_missing_or_invalid_csv_fails_before_connecting(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            input_directory = Path(temporary_directory)

            with self.subTest("missing customers file"), patch.object(
                load_raw, "OUTPUT_DIR", input_directory
            ), patch.object(load_raw, "connect_to_snowflake") as connect:
                with self.assertRaises(FileNotFoundError):
                    load_raw.main()
                connect.assert_not_called()

            with self.subTest("invalid customers schema"):
                (input_directory / "customers.csv").write_text(
                    "customer_id,unexpected_column\nC001,value\n",
                    encoding="utf-8",
                )
                with patch.object(
                    load_raw, "OUTPUT_DIR", input_directory
                ), patch.object(load_raw, "connect_to_snowflake") as connect:
                    with self.assertRaisesRegex(ValueError, "invalid schema"):
                        load_raw.main()
                    connect.assert_not_called()

    def test_required_nulls_fail_before_connecting_in_all_datasets(self):
        cases = [
            ("CUSTOMERS", "customers", "email"),
            ("PLANS", None, "PLAN_NAME"),
            ("SUBSCRIPTIONS", "subscriptions", "start_date"),
            ("PAYMENTS", "payments", "amount"),
            ("PRODUCT_EVENTS", "product_events", "event_timestamp"),
        ]

        for table_name, filename, column in cases:
            with self.subTest(dataset=table_name, column=column), \
                    tempfile.TemporaryDirectory() as temporary_directory:
                datasets = write_valid_inputs(temporary_directory)
                plans = None
                if filename is None:
                    plans = list(load_raw.PLANS)
                    plans[0] = (plans[0][0], None, *plans[0][2:])
                else:
                    datasets[filename].loc[0, column] = None
                    datasets[filename].to_csv(
                        Path(temporary_directory) / f"{filename}.csv",
                        index=False,
                    )
                with ExitStack() as stack:
                    stack.enter_context(
                        patch.object(
                            load_raw, "OUTPUT_DIR", Path(temporary_directory)
                        )
                    )
                    if plans is not None:
                        stack.enter_context(patch.object(load_raw, "PLANS", plans))
                    connect_mock = stack.enter_context(
                        patch.object(load_raw, "connect_to_snowflake")
                    )
                    with self.assertRaisesRegex(
                        ValueError, f"{table_name}.*{column.upper()}"
                    ):
                        load_raw.main()
                    connect_mock.assert_not_called()

    def test_nullable_end_date_and_event_properties_are_allowed(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            datasets = write_valid_inputs(temporary_directory)
            datasets["product_events"].loc[0, "event_properties"] = None
            datasets["product_events"].to_csv(
                Path(temporary_directory) / "product_events.csv", index=False
            )

            with patch.object(load_raw, "OUTPUT_DIR", Path(temporary_directory)):
                prepared = load_raw.prepare_input_data()

        self.assertTrue(pd.isna(prepared["SUBSCRIPTIONS"]["END_DATE"].iloc[0]))
        self.assertIsNone(prepared["PRODUCT_EVENTS"]["EVENT_PROPERTIES"].iloc[0])

    def test_invalid_date_fails_before_connecting(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            datasets = write_valid_inputs(temporary_directory)
            datasets["subscriptions"].loc[0, "start_date"] = "not-a-date"
            datasets["subscriptions"].to_csv(
                Path(temporary_directory) / "subscriptions.csv", index=False
            )

            with patch.object(
                load_raw, "OUTPUT_DIR", Path(temporary_directory)
            ), patch.object(load_raw, "connect_to_snowflake") as connect:
                with self.assertRaises(ValueError):
                    load_raw.main()
                connect.assert_not_called()

    def test_malformed_and_nonstandard_event_json_fails_before_connecting(self):
        invalid_values = ["{malformed", "NaN", "Infinity", "-Infinity"]
        for value in invalid_values:
            with self.subTest(value=value), tempfile.TemporaryDirectory() as temporary_directory:
                datasets = write_valid_inputs(temporary_directory)
                datasets["product_events"].loc[0, "event_properties"] = value
                datasets["product_events"].to_csv(
                    Path(temporary_directory) / "product_events.csv", index=False
                )

                with patch.object(
                    load_raw, "OUTPUT_DIR", Path(temporary_directory)
                ), patch.object(load_raw, "connect_to_snowflake") as connect:
                    with self.assertRaisesRegex(
                        ValueError, "PRODUCT_EVENTS.*EVENT_PROPERTIES"
                    ):
                        load_raw.main()
                    connect.assert_not_called()

    def test_temporary_load_failure_prevents_production_replacement(self):
        datasets = {table: [object()] for table in load_raw.TABLES}
        temporary_tables = {
            table: f"_LOAD_{table}_RUN" for table in load_raw.TABLES
        }
        connection = MagicMock()

        with patch.object(load_raw, "prepare_input_data", return_value=datasets), \
                patch.object(load_raw, "connect_to_snowflake", return_value=connection), \
                patch.object(load_raw, "create_temporary_tables", return_value=temporary_tables), \
                patch.object(
                    load_raw,
                    "load_temporary_tables",
                    side_effect=RuntimeError("temporary load failed"),
                ) as load_temporary, \
                patch.object(load_raw, "replace_raw_tables_atomically") as replace:
            with self.assertRaisesRegex(RuntimeError, "temporary load failed"):
                load_raw.main()

        load_temporary.assert_called_once()
        replace.assert_not_called()
        connection.close.assert_called_once()

    def test_row_count_mismatch_prevents_production_replacement(self):
        datasets = {table: [object()] for table in load_raw.TABLES}
        temporary_tables = {
            table: f"_LOAD_{table}_RUN" for table in load_raw.TABLES
        }
        connection = MagicMock()
        cursor = MagicMock()
        cursor.__enter__.return_value = cursor
        cursor.fetchone.return_value = (0,)
        connection.cursor.return_value = cursor

        with patch.object(load_raw, "prepare_input_data", return_value=datasets), \
                patch.object(load_raw, "connect_to_snowflake", return_value=connection), \
                patch.object(load_raw, "create_temporary_tables", return_value=temporary_tables), \
                patch.object(load_raw, "load_temporary_tables") as load_temporary, \
                patch.object(load_raw, "validate_counts", wraps=load_raw.validate_counts) as validate_counts, \
                patch.object(load_raw, "replace_raw_tables_atomically") as replace:
            with self.assertRaisesRegex(RuntimeError, "expected 1, got 0"):
                load_raw.main()

        load_temporary.assert_called_once()
        validate_counts.assert_called_once()
        replace.assert_not_called()

    def test_production_insert_failure_rolls_back_and_propagates(self):
        connection = MagicMock()
        cursor = MagicMock()
        connection.cursor.return_value = cursor
        original_error = RuntimeError("production insert failed")

        def execute(sql):
            if sql.lstrip().startswith("INSERT INTO"):
                raise original_error

        cursor.execute.side_effect = execute
        temporary_tables = {
            table: f"_LOAD_{table}_RUN" for table in load_raw.TABLES
        }

        with self.assertRaises(RuntimeError) as raised:
            load_raw.replace_raw_tables_atomically(connection, temporary_tables)

        self.assertIs(raised.exception, original_error)
        executed_sql = [call.args[0] for call in cursor.execute.call_args_list]
        self.assertEqual(executed_sql[-1], "ROLLBACK")
        cursor.close.assert_called_once()

    def test_row_count_validation_checks_all_five_datasets(self):
        connection = MagicMock()
        cursor = MagicMock()
        cursor.__enter__.return_value = cursor
        cursor.fetchone.side_effect = [(1,), (2,), (3,), (4,), (5,)]
        connection.cursor.return_value = cursor
        temporary_tables = {
            table: f"_LOAD_{table}_RUN" for table in load_raw.TABLES
        }
        expected_counts = {
            table: index
            for index, table in enumerate(load_raw.TABLES, start=1)
        }

        load_raw.validate_counts(connection, temporary_tables, expected_counts)

        count_queries = [
            call.args[0]
            for call in cursor.execute.call_args_list
            if call.args[0].startswith("SELECT COUNT(*)")
        ]
        self.assertEqual(len(count_queries), 5)
        for table in load_raw.TABLES:
            self.assertTrue(
                any(temporary_tables[table] in query for query in count_queries),
                f"{table} was not included in row-count validation",
            )


if __name__ == "__main__":
    unittest.main()
