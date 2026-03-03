#  Copyright 2022 Collate
#  Licensed under the Collate Community License, Version 1.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#  https://github.com/open-metadata/OpenMetadata/blob/main/ingestion/LICENSE
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""
Tibero E2E tests
"""

from typing import List

import pytest

from metadata.ingestion.api.status import Status

from .base.e2e_types import E2EType
from .common.test_cli_db import CliCommonDB
from .common_e2e_sqa_mixins import SQACommonMethods


class TiberoCliTest(CliCommonDB.TestSuite, SQACommonMethods):
    create_table_query: str = """
       CREATE TABLE tester.test_table (
         char_col      CHAR(10),
         varchar_col      VARCHAR(10),
         varchar2_col        VARCHAR2(10),
         nchar_col        NCHAR(10),
         nvarchar_col        NVARCHAR(10),
         raw_col   RAW(10),
         long_col      LONG,
         number_col  NUMBER(7,2),
         integer_col       INTEGER,
         float_col   FLOAT,
         date_col        DATE,
         timestamp_col        TIMESTAMP,
         timestamp_tz_col       TIMESTAMP WITH TIME ZONE,
         timestamp_ltz_col        TIMESTAMP WITH LOCAL TIME ZONE,
         interval_dts_col        INTERVAL DAY TO SECOND,
         clob_col        CLOB,
         blob_col        BLOB
       )
    """
    create_view_query: str = """
        CREATE OR REPLACE VIEW tester.test_view AS
        SELECT char_col,
    varchar_col,
    varchar2_col,
    nchar_col,
    nvarchar_col,
    raw_col,
    long_col,
    number_col,
    integer_col,
    float_col,
    date_col,
    timestamp_col,
    timestamp_tz_col,
    timestamp_ltz_col,
    interval_dts_col,
    clob_col,
    blob_col
    FROM tester.test_table
    """

    insert_data_queries: List[str] = [
        """
        INSERT INTO tester.test_table (
    char_col,
    varchar_col,
    varchar2_col,
    nchar_col,
    nvarchar_col,
    raw_col,
    long_col,
    number_col,
    integer_col,
    float_col,
    date_col,
    timestamp_col,
    timestamp_tz_col,
    timestamp_ltz_col,
    interval_dts_col,
    clob_col,
    blob_col
) WITH names AS (
SELECT 'CHAR_DATA',
    'varchar',
    'varchar2',
    N'abc',
    N'abc',
    HEXTORAW('DEADBEEF'),
    'LONG TEXT DATA',
    12345.67,
    100,
    123.456,
    DATE '2025-09-30',
    TIMESTAMP '2025-09-30 10:30:45',
    TIMESTAMP '2025-09-30 10:30:45 +09:00',
    TIMESTAMP '2025-09-30 10:30:45',
    INTERVAL '5 12:30:15' DAY TO SECOND,
    'CLOB sample data',
    EMPTY_BLOB()
)
SELECT * from names
""",
        """
INSERT INTO tester.test_table (
    char_col,
    varchar_col,
    varchar2_col,
    nchar_col,
    nvarchar_col,
    raw_col,
    long_col,
    number_col,
    integer_col,
    float_col,
    date_col,
    timestamp_col,
    timestamp_tz_col,
    timestamp_ltz_col,
    interval_dts_col,
    clob_col,
    blob_col
) WITH names AS (
SELECT 'CHAR_DATA',
    'varchar',
    'varchar2',
    N'abc',
    N'abc',
    HEXTORAW('DEADBEEF'),
    'LONG TEXT DATA',
    12345.67,
    100,
    123.456,
    DATE '2025-09-30',
    TIMESTAMP '2025-09-30 10:30:45',
    TIMESTAMP '2025-09-30 10:30:45 +09:00',
    TIMESTAMP '2025-09-30 10:30:45',
    INTERVAL '5 12:30:15' DAY TO SECOND,
    'CLOB sample data',
    EMPTY_BLOB()
)
SELECT * from names
""",
    ]

    drop_table_query: str = """
        DROP TABLE tester.test_table
    """

    drop_view_query: str = """
        DROP VIEW tester.test_view
    """

    def create_table_and_view(self) -> None:
        try:
            SQACommonMethods.create_table_and_view(self)
        except Exception:
            pass

    def delete_table_and_view(self) -> None:
        try:
            SQACommonMethods.delete_table_and_view(self)
        except Exception:
            pass

    @staticmethod
    def get_connector_name() -> str:
        return "tibero"

    @staticmethod
    def expected_tables() -> int:
        return 2

    @staticmethod
    def expected_profiled_tables() -> int:
        return 2

    def expected_sample_size(self) -> int:
        return 2

    def view_column_lineage_count(self) -> int:
        """view was created from `CREATE VIEW xyz AS (SELECT * FROM abc)`
        which does not propagate column lineage
        """
        return 17

    def expected_lineage_node(self) -> str:
        return "e2e_tibero.tibero.tester.test_view"

    @staticmethod
    def fqn_created_table() -> str:
        return "e2e_tibero.tibero.tester.TEST_TABLE"

    @staticmethod
    def _fqn_deleted_table() -> str:
        return "e2e_tibero.tibero.tester.TEST_TABLE"

    @staticmethod
    def get_includes_schemas() -> List[str]:
        return ["tester"]

    @staticmethod
    def get_includes_tables() -> List[str]:
        return ["test_table"]

    @staticmethod
    def get_excludes_tables() -> List[str]:
        return ["customers"]

    @staticmethod
    def expected_filtered_schema_includes() -> int:
        return 1

    @staticmethod
    def expected_filtered_schema_excludes() -> int:
        return 1

    @staticmethod
    def expected_filtered_table_includes() -> int:
        return 12

    @staticmethod
    def expected_filtered_table_excludes() -> int:
        return 12

    @staticmethod
    def expected_filtered_mix() -> int:
        return 12

    @pytest.mark.order(2)
    def test_create_table_with_profiler(self) -> None:
        # delete table in case it exists
        self.delete_table_and_view()
        # create a table and a view
        self.create_table_and_view()
        # build config file for ingest
        self.build_config_file(
            E2EType.INGEST_DB_FILTER_SCHEMA,
            {"includes": self.get_includes_schemas()},
        )
        # run ingest with new tables
        self.run_command()
        # build config file for profiler
        self.build_config_file(
            E2EType.PROFILER,
            # Otherwise the sampling here does not pick up rows
            extra_args={"profileSample": 1, "includes": self.get_includes_schemas()},
        )
        # run profiler with new tables
        result = self.run_command("profile")
        sink_status, source_status = self.retrieve_statuses(result)
        self.assert_for_table_with_profiler(source_status, sink_status)

    @pytest.mark.order(4)
    def test_delete_table_is_marked_as_deleted(self) -> None:
        """3. delete the new table + deploy marking tables as deleted

        We will perform the following steps:
            1. delete table created in previous test
            2. build config file for ingest
            3. run ingest `self.run_command()` defaults to `ingestion`
        """
        self.delete_table_and_view()
        self.build_config_file(
            E2EType.INGEST_DB_FILTER_SCHEMA,
            {
                "includes": self.get_includes_schemas()
            },
        )
        result = self.run_command()

        sink_status, source_status = self.retrieve_statuses(result)
        self.assert_for_delete_table_is_marked_as_deleted(source_status, sink_status)

    @pytest.mark.order(5)
    def test_schema_filter_includes(self) -> None:
        self.build_config_file(
            E2EType.INGEST_DB_FILTER_MIX,
            {
                "schema": {"includes": self.get_includes_schemas()},
                "table": {
                    "includes": self.get_includes_tables(),
                },
            },
        )
        result = self.run_command()

        sink_status, source_status = self.retrieve_statuses(result)
        self.assert_filtered_tables_includes(source_status, sink_status)

    @pytest.mark.order(6)
    def test_schema_filter_excludes(self) -> None:
        pass

    @pytest.mark.order(7)
    def test_table_filter_includes(self) -> None:
        """6. Vanilla ingestion + include table filter pattern

        We will perform the following steps:
            1. build config file for ingest with filters
            2. run ingest `self.run_command()` defaults to `ingestion`
        """
        self.build_config_file(
            E2EType.INGEST_DB_FILTER_MIX,
            {
                "schema": {"includes": self.get_includes_schemas()},
                "table": {"includes": self.get_includes_tables()},
            },
        )
        result = self.run_command()

        sink_status, source_status = self.retrieve_statuses(result)
        self.assert_filtered_tables_includes(source_status, sink_status)

    @pytest.mark.order(1)
    def test_vanilla_ingestion(self) -> None:
        """6. Vanilla ingestion

        We will perform the following steps:
            1. build config file for ingest with filters
            2. run ingest `self.run_command()` defaults to `ingestion`
        """
        self.build_config_file(
            E2EType.INGEST_DB_FILTER_SCHEMA,
            {"includes": self.get_includes_schemas()},
        )
        # run ingest with new tables
        result = self.run_command()
        sink_status, source_status = self.retrieve_statuses(result)
        self.assert_for_vanilla_ingestion(source_status, sink_status)

    @pytest.mark.order(8)
    def test_table_filter_excludes(self) -> None:
        """7. Vanilla ingestion + exclude table filter pattern

        We will perform the following steps:
            1. build config file for ingest with filters
            2. run ingest `self.run_command()` defaults to `ingestion`
        """

        self.build_config_file(
            E2EType.INGEST_DB_FILTER_MIX,
            {
                "schema": {"includes": self.get_includes_schemas()},
                "table": {"excludes": self.get_excludes_tables()},
            },
        )

        result = self.run_command()
        sink_status, source_status = self.retrieve_statuses(result)
        self.assert_filtered_tables_excludes(source_status, sink_status)

    @pytest.mark.order(11)
    def test_lineage(self) -> None:
        """10. Run queries in the source (creates, inserts, views) and ingest metadata & Lineage

        This test will need to be implemented on the database specific test classes
        """
        self.delete_table_and_view()
        self.create_table_and_view()
        self.build_config_file(
            E2EType.INGEST_DB_FILTER_SCHEMA,
            {"includes": self.get_includes_schemas()},
        )
        service_type = self.get_connector_name()
        if hasattr(self, "get_service_type"):
            service_type = self.get_service_type()

        self.run_command()
        self.build_config_file(
            E2EType.LINEAGE,
            {
                "source": f"{service_type}-lineage"
             },
        )
        result = self.run_command()
        sink_status, source_status = self.retrieve_statuses(result)
        self.assert_for_test_lineage(source_status, sink_status)

    def assert_for_vanilla_ingestion(
        self, source_status: Status, sink_status: Status
    ) -> None:
        self.assertEqual(len(source_status.failures), 0)
        self.assertEqual(len(source_status.warnings), 0)
        self.assertEqual(len(source_status.filtered), 15)
        self.assertGreaterEqual(
            (len(source_status.records) + len(source_status.updated_records)),
            self.expected_tables(),
        )
        self.assertEqual(len(sink_status.failures), 0)
        self.assertEqual(len(sink_status.warnings), 0)
        self.assertGreaterEqual(
            (len(sink_status.records) + len(sink_status.updated_records)),
            self.expected_tables(),
        )

    def assert_for_delete_table_is_marked_as_deleted(
            self, source_status: Status, sink_status: Status
    ):
        deleted_table = self.retrieve_table(self.fqn_deleted_table())

        if deleted_table is not None:
            self.assertTrue(deleted_table.deleted)

    @staticmethod
    def get_profiler_time_partition() -> dict:
        return {
            "fullyQualifiedName": "e2e_tibero.tibero.tester.test_table",
            "partitionConfig": {
                "partitionField": "date_col",  # 실제 시간 컬럼 이름
                "partitionInterval": 30,  # 최근 30일
                "partitionIntervalUnit": "DAY",  # 단위는 DAY
                "partitionFieldFormat": "yyyy-MM-dd"  # 컬럼의 문자열 포맷
            }
        }