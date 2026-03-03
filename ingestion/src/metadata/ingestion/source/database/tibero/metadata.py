import traceback

from typing import Type
from typing import Iterable, Optional

from sqlalchemy_tibero.base import INTERVAL, TiberoDialect, ischema_names
from sqlalchemy.types import TEXT
from sqlalchemy.engine import Inspector

from metadata.ingestion.source.database.column_type_parser import create_sqlalchemy_type

from metadata.generated.schema.entity.services.connections.database.tiberoConnection import TiberoConnection
from metadata.ingestion.source.database.common_db_source import (
    CommonDbSourceService,
)
from metadata.generated.schema.api.data.createStoredProcedure import (
    CreateStoredProcedureRequest,
)
from metadata.ingestion.source.database.tibero.models import (
    FetchObjectList,
    TiberoStoredObject,
)
from metadata.ingestion.source.database.tibero.queries import (
    TIBERO_GET_STORED_PACKAGES,
    TIBERO_GET_STORED_PROCEDURES,
)
from metadata.ingestion.ometa.ometa_api import OpenMetadata
from metadata.generated.schema.metadataIngestion.workflow import Source as WorkflowSource
from metadata.generated.schema.type.basic import EntityName
from metadata.ingestion.api.models import Either
from metadata.ingestion.api.steps import InvalidSourceException
from metadata.generated.schema.entity.data.databaseSchema import DatabaseSchema
from metadata.generated.schema.entity.data.storedProcedure import (
    Language,
    StoredProcedureCode,
    StoredProcedureType,
)
from metadata.generated.schema.entity.services.ingestionPipelines.status import (
    StackTraceError,
)
from metadata.utils import fqn

from metadata.ingestion.source.database.tibero.utils import (
    _get_col_type,
    _get_constraint_data,
    get_columns,
    get_mview_names,
    get_mview_names_dialect,
    get_table_comment,
    get_table_names,
    get_all_view_definitions,
    get_view_definition,
    get_view_names,
    get_view_names_dialect,
)
from metadata.utils.sqlalchemy_utils import (
    get_all_table_comments,
    get_all_table_ddls,
    get_table_ddl,
)


ischema_names.update(
    {
        "ROWID": create_sqlalchemy_type("ROWID"),
        "XMLTYPE": create_sqlalchemy_type("XMLTYPE"),
        "INTERVAL YEAR TO MONTH": TEXT,
    }
)

TiberoDialect.get_table_comment = get_table_comment
TiberoDialect.get_columns = get_columns
TiberoDialect._get_col_type = _get_col_type
TiberoDialect.get_view_definition = get_view_definition
TiberoDialect.get_all_view_definitions = get_all_view_definitions
TiberoDialect.get_all_table_comments = get_all_table_comments
TiberoDialect.get_table_names = get_table_names
Inspector.get_mview_names = get_mview_names
TiberoDialect.get_mview_names = get_mview_names_dialect
Inspector.get_view_names = get_view_names
TiberoDialect.get_view_names = get_view_names_dialect

Inspector.get_all_table_ddls = get_all_table_ddls
Inspector.get_table_ddl = get_table_ddl

TiberoDialect._get_constraint_data = _get_constraint_data


class TiberoSource(CommonDbSourceService):
    """
    Implements the necessary logic to ingest metadata from tibero DB.
    """

    @classmethod
    def create(cls, config_dict, metadata: OpenMetadata, pipeline_name: Optional[str] = None):
        config = WorkflowSource.model_validate(config_dict)
        connection: TiberoConnection = config.serviceConnection.root.config
        if not isinstance(connection, TiberoConnection):
            raise InvalidSourceException(
                f"Expected TiberoConnection, but got {connection}"
            )
        return cls(config, metadata)

    def process_result(self, data: FetchObjectList):
        """Process data as per our stored procedure format"""
        result_dict = {}

        for row in data:

            owner, name, line, text, procedure_type = row
            key = (owner, name)
            if key not in result_dict:
                result_dict[key] = {"lines": [], "text": "", "procedure_type": ""}
            result_dict[key]["lines"].append(line)
            result_dict[key]["text"] += text
            result_dict[key]["procedure_type"] = procedure_type

        # Return the concatenated text for each procedure name, ordered by line
        return result_dict

    def _get_stored_procedures_internal(
        self, query: str
    ) -> Iterable[TiberoStoredObject]:
        results: FetchObjectList = self.engine.execute(
            query.format(schema=self.context.get().database_schema.upper())
        ).all()
        results = self.process_result(data=results)
        for row in results.items():
            stored_procedure = TiberoStoredObject(
                name=row[0][1],
                definition=row[1]["text"],
                owner=row[0][0],
                procedure_type=row[1]["procedure_type"],
            )
            yield stored_procedure

    def get_stored_procedures(self) -> Iterable[TiberoStoredObject]:
        """List Oracle Stored Procedures"""
        if self.source_config.includeStoredProcedures:
            yield from self._get_stored_procedures_internal(
                TIBERO_GET_STORED_PROCEDURES
            )
            yield from self._get_stored_procedures_internal(TIBERO_GET_STORED_PACKAGES)


    def yield_stored_procedure(
        self, stored_procedure: TiberoStoredObject
    ) -> Iterable[Either[CreateStoredProcedureRequest]]:
        """Prepare the stored procedure payload"""
        try:
            stored_procedure_request = CreateStoredProcedureRequest(
                name=EntityName(stored_procedure.name),
                storedProcedureCode=StoredProcedureCode(
                    language=Language.SQL,
                    code=stored_procedure.definition,
                ),
                storedProcedureType=(
                    StoredProcedureType.StoredPackage
                    if stored_procedure.procedure_type == "StoredPackage"
                    else StoredProcedureType.StoredProcedure
                ),
                owners=self.metadata.get_reference_by_name(
                    name=stored_procedure.owner.lower(), is_owner=True
                ),
                databaseSchema=fqn.build(
                    metadata=self.metadata,
                    entity_type=DatabaseSchema,
                    service_name=self.context.get().database_service,
                    database_name=self.context.get().database,
                    schema_name=self.context.get().database_schema,
                ),
            )
            yield Either(right=stored_procedure_request)
            self.register_record_stored_proc_request(stored_procedure_request)
        except Exception as exc:
            yield Either(
                left=StackTraceError(
                    name=stored_procedure.name,
                    error=f"Error yielding Stored Procedure [{stored_procedure.name}] due to [{exc}]",
                    stackTrace=traceback.format_exc(),
                )
            )