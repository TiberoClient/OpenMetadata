import re

from sqlalchemy import sql, util
from sqlalchemy_tibero import FLOAT, INTERVAL, NUMBER, TIMESTAMP
from sqlalchemy.engine import reflection
from sqlalchemy.sql import sqltypes
from sqlalchemy.types import INTEGER

from metadata.ingestion.source.database.tibero.queries import (
    GET_MATERIALIZED_VIEW_NAMES,
    GET_VIEW_NAMES,
    TIBERO_ALL_CONSTRAINTS,
    TIBERO_ALL_TABLE_COMMENTS,
    TIBERO_ALL_VIEW_DEFINITIONS,
    TIBERO_GET_COLUMNS,
    TIBERO_GET_TABLE_NAMES,
    TIBERO_IDENTITY_TYPE,
)
from metadata.utils.sqlalchemy_utils import (
    get_table_comment_wrapper,
    get_view_definition_wrapper,
)

@reflection.cache
def get_table_comment(
    self,
    connection,
    table_name: str,
    schema: str = None,
    resolve_synonyms=False,
    dblink="",
    **kw,
):
    return get_table_comment_wrapper(
        self,
        connection,
        table_name=table_name.lower(),
        schema=schema.lower() if schema else None,
        query=TIBERO_ALL_TABLE_COMMENTS,
    )

@reflection.cache
def get_all_view_definitions(self, connection, query):
    """
    Method to fetch view definition of all available views
    """
    self.all_view_definitions = {}
    self.current_db: str = connection.engine.url.database  # type: ignore
    result = connection.execute(query)
    for view in result:
        if hasattr(view, "view_def") and hasattr(view, "schema"):
            self.all_view_definitions[
                (view.view_name, view.schema)
            ] = f"CREATE OR REPLACE VIEW {view.view_name} AS {view.view_def}"
        elif hasattr(view, "VIEW_DEF") and hasattr(view, "SCHEMA"):
            self.all_view_definitions[
                (view.VIEW_NAME, view.SCHEMA)
            ] = f"CREATE OR REPLACE VIEW {view.VIEW_NAME} AS {view.VIEW_DEF}"

@reflection.cache
def get_view_definition(
    self,
    connection,
    view_name: str,
    schema: str = None,
    resolve_synonyms=False,
    dblink="",
    **kw,
):
    return get_view_definition_wrapper(
        self,
        connection,
        table_name=view_name.lower(),
        schema=schema.lower() if schema else None,
        query=TIBERO_ALL_VIEW_DEFINITIONS,
    )

def _get_col_type(
    self, coltype, precision, scale, length, colname
):  # pylint: disable=too-many-branches
    raw_type = coltype
    if coltype == "NUMBER":
        coltype = NUMBER(precision, scale)
        if precision is not None:
            if scale is not None:
                if scale > 0:
                    raw_type += f"({int(precision)},{int(scale)})"
                else:
                    if precision == 38 and scale == 0:
                        coltype = INTEGER()
                    raw_type += f"({int(precision)})"
    elif coltype == "FLOAT":
        coltype = FLOAT()
    elif coltype in ("VARCHAR", "NVARCHAR", "CHAR", "NCHAR"):
        coltype = self.ischema_names.get(coltype)(length)
        if length:
            raw_type += f"({int(length)})"
    elif "WITH TIME ZONE" in coltype or "TIMESTAMP" in coltype:
        coltype = TIMESTAMP(timezone=True)
    elif "INTERVAL" in coltype:
        coltype = INTERVAL()
    else:
        coltype = re.sub(r"\(\d+\)", "", coltype)
        try:
            coltype = self.ischema_names[coltype]
        except KeyError:
            util.warn(f"Did not recognize type '{coltype}' of column '{colname}'")
            coltype = sqltypes.NULLTYPE
    return coltype, raw_type

# pylint: disable=too-many-locals
@reflection.cache
def get_columns(self, connection, table_name, schema=None, **kw):
    """

    Dialect method overridden to add raw data type

    kw arguments can be:

        tibero_resolve_synonyms

        dblink

    """
    resolve_synonyms = kw.get("tibero_resolve_synonyms", False)
    dblink = kw.get("dblink", "")
    info_cache = kw.get("info_cache")

    (table_name, schema, dblink, _) = self._prepare_reflection_args(
        connection,
        table_name,
        schema,
        resolve_synonyms,
        dblink,
        info_cache=info_cache,
    )
    columns = []

    char_length_col = "data_length"
    if self._supports_char_length:
        char_length_col = "char_length"

    identity_cols = """\
                NULL as default_on_null,
                (
                    SELECT id.generation_type || ',' || id.IDENTITY_OPTIONS
                    FROM ALL_TAB_IDENTITY_COLS%(dblink)s id
                    WHERE col.table_name = id.table_name
                    AND col.column_name = id.column_name
                    AND col.owner = id.owner
                ) AS identity_options""" % {
        "dblink": dblink
    }

    params = {"table_name": table_name}

    text = TIBERO_GET_COLUMNS.format(
        dblink=dblink, char_length_col=char_length_col, identity_cols=identity_cols
    )
    if schema is not None:
        params["owner"] = schema
        text += " AND col.owner = :owner "
    text += " ORDER BY col.column_id"

    cols = connection.execute(sql.text(text), params)

    for row in cols:
        colname = self.normalize_name(row[0])
        length = row[2]
        nullable = row[5] == "Y"
        default = row[6]
        generated = row[8]
        default_on_nul = row[9]
        identity_options = row[10]

        coltype, raw_coltype = self._get_col_type(
            row.data_type, row.data_precision, row.data_scale, length, colname
        )

        computed = None
        if generated == "YES":
            computed = {"sqltext": default}
            default = None

        identity = None
        if identity_options is not None:
            identity = self._parse_identity_options(identity_options, default_on_nul)
            default = None

        cdict = {
            "name": colname,
            "type": coltype,
            "nullable": nullable,
            "default": default,
            "autoincrement": "auto",
            "comment": row.comments,
            "system_data_type": raw_coltype,
        }
        if row.column_name.lower() == row.column_name:
            cdict["quote"] = True
        if computed is not None:
            cdict["computed"] = computed
        if identity is not None:
            cdict["identity"] = identity

        columns.append(cdict)
    return columns

@reflection.cache
def get_table_names(self, connection, schema=None, **kw):
    """
    Exclude the materialized views from regular table names
    """
    schema = self.denormalize_name(schema or self.default_schema_name)

    # note that table_names() isn't loading DBLINKed or synonym'ed tables
    if schema is None:
        schema = self.default_schema_name

    tablespace = ""

    if self.exclude_tablespaces:
        exclude_tablespace = ", ".join([f"'{ts}'" for ts in self.exclude_tablespaces])
        tablespace = (
            "nvl(tablespace_name, 'no tablespace') "
            f"NOT IN ({exclude_tablespace}) AND "
        )
    sql_str = TIBERO_GET_TABLE_NAMES.format(tablespace=tablespace)
    cursor = connection.execute(sql.text(sql_str), {"owner": schema})
    return [row[0] for row in cursor]


def get_view_names(self, schema=None):
    """Return all materialized view names in `schema`.

    :param schema: Optional, retrieve names from a non-default schema.
        For special quoting, use :class:`.quoted_name`.

    """

    with self._operation_context() as conn:
        return self.dialect.get_view_names(conn, schema, info_cache=self.info_cache)


@reflection.cache
def get_view_names_dialect(self, connection, schema=None, **kw):
    schema = self.denormalize_name(schema or self.default_schema_name)
    sql_query = sql.text(GET_VIEW_NAMES)
    cursor = connection.execute(sql_query, {"owner": self.denormalize_name(schema)})
    return [self.normalize_name(row[0]) for row in cursor]


def get_mview_names(self, schema=None):
    """Return all materialized view names in `schema`.

    :param schema: Optional, retrieve names from a non-default schema.
        For special quoting, use :class:`.quoted_name`.

    """

    with self._operation_context() as conn:
        return self.dialect.get_mview_names(conn, schema, info_cache=self.info_cache)


@reflection.cache
def get_mview_names_dialect(self, connection, schema=None, **kw):
    schema = self.denormalize_name(schema or self.default_schema_name)
    sql_query = sql.text(GET_MATERIALIZED_VIEW_NAMES)
    cursor = connection.execute(sql_query, {"owner": self.denormalize_name(schema)})
    return [self.normalize_name(row[0]) for row in cursor]


@reflection.cache
def _get_constraint_data(self, connection, table_name, schema=None, dblink="", **kw):

    params = {"table_name": table_name, "owner": schema}
    text = TIBERO_ALL_CONSTRAINTS.format(dblink=dblink)

    rp = connection.execute(sql.text(text), params)
    constraint_data = rp.fetchall()
    return constraint_data


