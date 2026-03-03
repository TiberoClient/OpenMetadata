#  Copyright 2025 Collate
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
Test Tibero using the topology
"""

from unittest import TestCase
from unittest.mock import patch

from metadata.generated.schema.api.data.createDatabase import CreateDatabaseRequest
from metadata.generated.schema.api.data.createDatabaseSchema import (
    CreateDatabaseSchemaRequest,
)
from metadata.generated.schema.api.data.createStoredProcedure import (
    CreateStoredProcedureRequest,
)
from metadata.generated.schema.entity.data.database import Database
from metadata.generated.schema.entity.data.databaseSchema import DatabaseSchema
from metadata.generated.schema.entity.data.storedProcedure import (
    StoredProcedureCode,
    StoredProcedureType,
)
from metadata.generated.schema.entity.services.connections.metadata.openMetadataConnection import (
    OpenMetadataConnection,
)
from metadata.generated.schema.entity.services.databaseService import (
    DatabaseConnection,
    DatabaseService,
    DatabaseServiceType,
)
from metadata.generated.schema.metadataIngestion.workflow import (
    OpenMetadataWorkflowConfig,
)
from metadata.generated.schema.type.basic import EntityName, FullyQualifiedEntityName
from metadata.generated.schema.type.entityReference import EntityReference
from metadata.ingestion.ometa.ometa_api import OpenMetadata
from metadata.ingestion.source.database.tibero.metadata import TiberoSource
from metadata.ingestion.source.database.tibero.models import TiberoStoredObject
from metadata.generated.schema.entity.services.connections.database.tiberoConnection import TiberoConnection


mock_tibero_config = {
    "source": {
        "type": "tibero",
        "serviceName": "test2",
        "serviceConnection": {
            "config": {
                "type": "Tibero",
                "username": "test_user",
                "password": "test_password",
                "databaseName": "test_db",
                "hostPort": "localhost:8629",
                "scheme": "tibero+pyodbc",
                "supportsMetadataExtraction": "true",
            }
        },
        "sourceConfig": {"config": {"type": "DatabaseMetadata"}},
    },
    "sink": {"type": "metadata-rest", "config": {}},
    "workflowConfig": {
        "openMetadataServerConfig": {
            "hostPort": "http://localhost:8585/api",
            "authProvider": "openmetadata",
            "securityConfig": {"jwtToken": "eyJraWQiOiJHYjM4OWEtOWY3Ni1nZGpzLWE5MmotMDI0MmJrOTQzNTYiLCJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJvcGVuLW1ldGFkYXRhLm9yZyIsInN1YiI6InRpYmVybyIsInJvbGVzIjpbIkFkbWluIl0sImVtYWlsIjoidGliZXJvQHRtYXguY28ua3IiLCJpc0JvdCI6ZmFsc2UsInRva2VuVHlwZSI6IlBFUlNPTkFMX0FDQ0VTUyIsImlhdCI6MTc1ODUxNDA1MiwiZXhwIjoxNzY2MjkwMDUyfQ.TfWHpUamOy-tUMBhG_MwCVWJPeWVcG15QGis-VzyzV9iRZLCrK_7WnM8C7OcsUHMzdB2dPdlBlbnH2xZyAJ6BIQqyLtvcacUeSF1gW29V-iLXZ9DmzVgJcPVjeMnOcMtvFTcCUomJFkQ0N5tW4B_sZbSGQ2tWDDyzUfq0w2f_w9wAcYh83Gy_EM2It2XL1QCfZuUU1ffZ2ktp36LYSGeg0WPRyAq-B-lMz6pXun4vP-CdT04QEBhK6TW9yZfPtuzSMK0SbuyB68D9xXFRK6efw48nvoYwNwYwWeGbkw-i9bBL6Bx0MNSVluciMV01gjtcyMnolyzw7eix959u_XsYA"},
        }
    },
}

MOCK_DATABASE_SERVICE = DatabaseService(
    id="c3eb265f-5445-4ad3-ba5e-797d3a3071bb",
    name="tibero_source_test",
    connection=DatabaseConnection(),
    serviceType=DatabaseServiceType.Tibero,
)

MOCK_DATABASE = Database(
    id="a58b1856-729c-493b-bc87-6d2269b43ec0",
    name="sample_database",
    fullyQualifiedName="tibero_source_test.sample_database",
    displayName="sample_database",
    description="",
    service=EntityReference(
        id="85811038-099a-11ed-861d-0242ac120002", type="databaseService"
    ),
)

MOCK_DATABASE_SCHEMA = DatabaseSchema(
    id="c3eb265f-5445-4ad3-ba5e-797d3a3071bb",
    name="sample_schema",
    fullyQualifiedName="mssql_source_test.sample_database.sample_schema",
    service=EntityReference(id="c3eb265f-5445-4ad3-ba5e-797d3a3071bb", type="database"),
    database=EntityReference(
        id="a58b1856-729c-493b-bc87-6d2269b43ec0",
        type="database",
    ),
)

MOCK_STORED_PROCEDURE = TiberoStoredObject(
    name="sample_procedure",
    definition="SAMPLE_SQL_TEXT",
    owner="sample_stored_prcedure_owner",
    procedure_type="StoredProcedure",
)

MOCK_STORED_PACKAGE = TiberoStoredObject(
    name="sample_package",
    definition="SAMPLE_SQL_TEXT",
    owner="sample_stored_package_owner",
    procedure_type="StoredPackage",
)

EXPECTED_DATABASE = [
    CreateDatabaseRequest(
        name=EntityName("sample_database"),
        service=FullyQualifiedEntityName("tibero_source_test"),
        default=False,
    )
]

EXPECTED_DATABASE_SCHEMA = [
    CreateDatabaseSchemaRequest(
        name=EntityName("sample_schema"),
        database=FullyQualifiedEntityName("tibero_source_test.sample_database"),
    )
]

EXPECTED_STORED_PROCEDURE = [
    CreateStoredProcedureRequest(
        name=EntityName("sample_procedure"),
        storedProcedureCode=StoredProcedureCode(language="SQL", code="SAMPLE_SQL_TEXT"),
        storedProcedureType=StoredProcedureType.StoredProcedure,
        databaseSchema=FullyQualifiedEntityName(
            "tibero_source_test.sample_database.sample_schema"
        ),
    )
]

EXPECTED_STORED_PACKAGE = [
    CreateStoredProcedureRequest(
        name=EntityName("sample_package"),
        storedProcedureCode=StoredProcedureCode(language="SQL", code="SAMPLE_SQL_TEXT"),
        storedProcedureType=StoredProcedureType.StoredPackage,
        databaseSchema=FullyQualifiedEntityName(
            "tibero_source_test.sample_database.sample_schema"
        ),
    )
]


class TiberoUnitTest(TestCase):
    """
    Implements the necessary methods to extract
    Tibero Unit Test
    """

    @patch(
        "metadata.ingestion.source.database.common_db_source.CommonDbSourceService.test_connection"
    )
    def __init__(
        self,
        methodName,
        test_connection,
    ) -> None:
        super().__init__(methodName)
        test_connection.return_value = False
        self.config = OpenMetadataWorkflowConfig.model_validate(mock_tibero_config)
        self.metadata = OpenMetadata(
            OpenMetadataConnection.model_validate(
                mock_tibero_config["workflowConfig"]["openMetadataServerConfig"]
            )
        )
        self.tibero = TiberoSource.create(
            mock_tibero_config["source"],
            self.metadata,
        )
        self.tibero.context.get().__dict__[
            "database_service"
        ] = MOCK_DATABASE_SERVICE.name.root

    def test_yield_database(self):
        assert EXPECTED_DATABASE == [
            either.right
            for either in self.tibero.yield_database(MOCK_DATABASE.name.root)
        ]

        self.tibero.context.get().__dict__["database"] = MOCK_DATABASE.name.root

    def test_yield_schema(self):
        assert EXPECTED_DATABASE_SCHEMA == [
            either.right
            for either in self.tibero.yield_database_schema(
                MOCK_DATABASE_SCHEMA.name.root
            )
        ]
        self.tibero.context.get().__dict__[
            "database_schema"
        ] = MOCK_DATABASE_SCHEMA.name.root

    def test_yield_stored_procedure(self):
        assert EXPECTED_STORED_PROCEDURE == [
            either.right
            for either in self.tibero.yield_stored_procedure(MOCK_STORED_PROCEDURE)
        ]

    def test_yield_stored_package(self):
        assert EXPECTED_STORED_PACKAGE == [
            either.right
            for either in self.tibero.yield_stored_procedure(MOCK_STORED_PACKAGE)
        ]
