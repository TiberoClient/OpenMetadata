# Tibero

In this section, we provide guides and references to use the Tibero connector.

## Requirements

$$note
To retrieve metadata from a Tibero database, the `tibero` library is used, which provides support for Tibero7.
$$

To ingest metadata from Tibero, the user must have the following permissions:
- `CREATE SESSION` privilege for the user.

```sql
-- CREATE USER
CREATE USER user_name IDENTIFIED BY admin_password;

-- GRANT CREATE SESSION PRIVILEGE TO USER
GRANT CREATE SESSION TO user_name;

-- GRANT SELECT CATALOG ROLE PRIVILEGE TO FETCH METADATA TO USER
GRANT SELECT_CATALOG_ROLE TO user_name;
```

- `GRANT SELECT` on the relevant tables which are to be ingested into OpenMetadata to the user
```sql
GRANT SELECT ON table_name TO user_name;
```

### Profiler & Data Quality
Executing the profiler Workflow or data quality tests, will require the user to have `SELECT` permission on the tables/schemas where the profiler/tests will be executed. More information on the profiler workflow setup can be found [here](https://docs.open-metadata.org/how-to-guides/data-quality-observability/profiler/workflow) and data quality tests [here](https://docs.open-metadata.org/connectors/ingestion/workflows/data-quality).

### Usage & Lineage
For the usage and lineage workflow, the user will need `SELECT` privilege. You can find more information on the usage workflow [here](https://docs.open-metadata.org/connectors/ingestion/workflows/usage) and the lineage workflow [here](https://docs.open-metadata.org/connectors/ingestion/workflows/lineage).

## Connection Details

$$section
### Scheme $(id="scheme")

**tibero+pyodbc**: SQLAlchemy scheme to connect to Tibero.
$$

$$section
### Username $(id="username")

Username to connect to Tibero. This user should have privileges to read all the metadata in Tibero.
$$

$$section
### Password $(id="password")

Password to connect to Tibero.
$$

$$section
### Host Port $(id="hostPort")

This parameter specifies the host and port of the Tibero instance. This should be specified as a string in the format `hostname:port`. For example, you might set the hostPort parameter to `localhost:8629`.

If you are running the OpenMetadata ingestion in a docker and your services are hosted on the `localhost`, then use `host.docker.internal:8629` as the value.
ex. `172.17.0.1:8629`
$$

$$section
### Database Name $(id="databaseName")

The name of the database to connect to in Tibero.
$$

$$section
### Driver $(id="driver")

The ODBC driver name for Tibero. Default is `Tibero7Driver`.
$$

$$section
### Connection Options $(id="connectionOptions")

Enter the details for any additional connection options that can be sent to Tibero during the connection. These details must be added as Key-Value pairs.
$$

$$section
### Connection Arguments $(id="connectionArguments")

Enter the details for any additional connection arguments such as security or protocol configs that can be sent to Tibero during the connection. These details must be added as Key-Value pairs.
$$

