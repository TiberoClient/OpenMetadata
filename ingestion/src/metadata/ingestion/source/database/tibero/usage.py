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
  type: tibero-usage
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

from metadata.ingestion.source.database.tibero.queries import (
    TIBERO_QUERY_HISTORY_STATEMENT,
)
from metadata.ingestion.source.database.tibero.query_parser import (
    TiberoQueryParserSource,
)
from metadata.ingestion.source.database.usage_source import UsageSource


class TiberoUsageSource(TiberoQueryParserSource, UsageSource):
    filters = ""  # No further filtering in the queries

    sql_stmt = TIBERO_QUERY_HISTORY_STATEMENT
