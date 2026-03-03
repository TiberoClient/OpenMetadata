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
Tibero lineage module

Execute with

source:
  type: tibero-lineage
  serviceName: tibero
  sourceConfig:
    config:
      queryLogDuration: 1
sink:
  type: metadata-rest
  config: {}
workflowConfig:
  openMetadataServerConfig:
    hostPort: http://localhost:8585/api
    authProvider: openmetadata
    securityConfig:
      jwtToken: "token"
"""

from typing import Dict, List

from metadata.ingestion.source.database.lineage_source import LineageSource
from metadata.ingestion.source.database.tibero.queries import (
    TIBERO_GET_STORED_PROCEDURE_QUERIES,
    TIBERO_QUERY_HISTORY_STATEMENT,
)
from metadata.ingestion.source.database.tibero.query_parser import (
    TiberoQueryParserSource,
)
from metadata.ingestion.source.database.stored_procedures_mixin import (
    QueryByProcedure,
    StoredProcedureLineageMixin,
)
from metadata.utils.helpers import get_start_and_end


class TiberoLineageSource(
    TiberoQueryParserSource, StoredProcedureLineageMixin, LineageSource
):
    filters = """AND (
            lower(SQL_TEXT) LIKE '%%create%%as%%select%%'
            OR lower(SQL_TEXT) LIKE '%%insert%%into%%select%%'
            OR lower(SQL_TEXT) LIKE '%%update%%'
            OR lower(SQL_TEXT) LIKE '%%merge%%'
        )"""

    sql_stmt = TIBERO_QUERY_HISTORY_STATEMENT

    stored_procedure_query = TIBERO_GET_STORED_PROCEDURE_QUERIES

    def get_stored_procedure_sql_statement(self) -> str:
        """
        Return the dictionary associating stored procedures to the
        queries they triggered
        """
        start, _ = get_start_and_end(self.source_config.queryLogDuration)
        query = self.stored_procedure_query.format(
            start_date=start,
        )

        return query
