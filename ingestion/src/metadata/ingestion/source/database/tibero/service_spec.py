from metadata.ingestion.source.database.tibero.connection import TiberoConnection
from metadata.ingestion.source.database.tibero.metadata import TiberoSource
from metadata.ingestion.source.database.tibero.lineage import TiberoLineageSource
from metadata.ingestion.source.database.tibero.usage import TiberoUsageSource
from metadata.utils.service_spec.default import DefaultDatabaseSpec

ServiceSpec = DefaultDatabaseSpec(
    metadata_source_class=TiberoSource,
    lineage_source_class=TiberoLineageSource,
    usage_source_class=TiberoUsageSource,
    connection_class=TiberoConnection
)
