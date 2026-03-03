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
Source connection handler
"""
from copy import deepcopy
from typing import Optional
from urllib.parse import quote_plus

from pydantic import SecretStr
from sqlalchemy.engine import Engine

from metadata.generated.schema.entity.automations.workflow import (
    Workflow as AutomationWorkflow,
)
from metadata.generated.schema.entity.services.connections.database.tiberoConnection import (
    TiberoConnection as TiberoConnectionConfig,
)
from metadata.generated.schema.entity.services.connections.testConnectionResult import (
    TestConnectionResult,
)
from metadata.ingestion.connections.builders import (
    create_generic_db_connection,
    get_connection_args_common,
    get_connection_options_dict,
)
from metadata.ingestion.connections.connection import BaseConnection
from metadata.ingestion.connections.secrets import connection_with_options_secrets
from metadata.ingestion.connections.test_connections import test_connection_db_common
from metadata.ingestion.ometa.ometa_api import OpenMetadata
from metadata.ingestion.source.database.tibero.queries import (
    CHECK_ACCESS_TO_ALL,
    TEST_TIBERO_GET_STORED_PACKAGES,
)
from metadata.utils.constants import THREE_MIN
from metadata.utils.logger import ingestion_logger

logger = ingestion_logger()

class TiberoConnection(BaseConnection[TiberoConnectionConfig, Engine]):
    def __init__(self, connection: TiberoConnectionConfig):
        super().__init__(connection)

    def _get_client(self) -> Engine:
        """
        Create connection
        """
        return create_generic_db_connection(
            connection=self.service_connection,
            get_connection_url_fn=self.get_connection_url,
            get_connection_args_fn=get_connection_args_common,
        )

    def get_connection_dict(self) -> dict:
        """
        Return the connection dictionary for this service.
        """
        url = self.client.url
        connection_copy = deepcopy(self.service_connection)

        connection_dict = {
            "driver": url.drivername,
            "host": f"{url.host}:{url.port}",  # This is the format expected by data-diff. If we start using this for something else, we need to change it and modify the data-diff code.
            "user": url.username,
        }

        # Add password if present in the connection
        if connection_copy.password:
            connection_dict["password"] = connection_copy.password.get_secret_value()

        # Add database name
        if connection_copy.databaseName:
            connection_dict["database"] = connection_copy.databaseName

        # Add connection options if present
        if connection_copy.connectionOptions and connection_copy.connectionOptions.root:
            connection_with_options_secrets(lambda: connection_copy)
            connection_dict.update(connection_copy.connectionOptions.root)

        # Add connection arguments if present
        if (
            connection_copy.connectionArguments
            and connection_copy.connectionArguments.root
        ):
            connection_dict.update(get_connection_args_common(connection_copy))

        return connection_dict

    @staticmethod
    def get_connection_url(connection: TiberoConnectionConfig) -> str:
        """
        Build the SQLConnection URL for the database connection
        """
        url = f"{connection.scheme.value}://"

        if connection.username:
            url += f"{quote_plus(connection.username)}"
            if not connection.password:
                connection.password = SecretStr("")
            url += f":{quote_plus(connection.password.get_secret_value())}"
            url += "@"

        if connection.hostPort:
            url += connection.hostPort

        if connection.databaseName:
            url += f"/{connection.databaseName}"

        if connection.driver:
            url += f"?Driver={quote_plus(connection.driver)}"

        options = get_connection_options_dict(connection)
        if options:
            separator = "&" if connection.driver else "?"
            params = "&".join(
                f"{key}={quote_plus(str(value))}"
                for (key, value) in options.items()
                if value
            )
            if params:
                url = f"{url}{separator}{params}"

        return url


    def test_connection(
        self,
        metadata: OpenMetadata,
        automation_workflow: Optional[AutomationWorkflow] = None,
        timeout_seconds: Optional[int] = THREE_MIN,
    ) -> TestConnectionResult:
        """
        Test connection. This can be executed either as part
        of a metadata workflow or during an Automation Workflow
        """

        test_conn_queries = {
            "CheckAccess": CHECK_ACCESS_TO_ALL,
            "PackageAccess": TEST_TIBERO_GET_STORED_PACKAGES,
        }

        return test_connection_db_common(
            metadata=metadata,
            engine=self.client,
            service_connection=self.service_connection,
            automation_workflow=automation_workflow,
            queries=test_conn_queries,
            timeout_seconds=timeout_seconds,
        )
