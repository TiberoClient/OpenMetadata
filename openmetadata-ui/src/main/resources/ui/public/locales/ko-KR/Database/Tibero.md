# Tibero

이 섹션에서는 Tibero 커넥터 사용을 위한 가이드와 참고 자료를 제공합니다.

## 요구사항

$$note
Tibero 데이터베이스에서 메타데이터를 가져오기 위해 `tibero` 라이브러리가 사용되며, Tibero7을 지원합니다.
$$

Tibero에서 메타데이터를 수집하려면 사용자에게 다음 권한이 필요합니다:
- 사용자에게 `CREATE SESSION` 권한이 필요합니다.

```sql
-- 사용자 생성
CREATE USER user_name IDENTIFIED BY admin_password;

-- 사용자에게 CREATE SESSION 권한 부여
GRANT CREATE SESSION TO user_name;

-- 메타데이터를 가져오기 위해 사용자에게 SELECT_CATALOG_ROLE 권한 부여
GRANT SELECT_CATALOG_ROLE TO user_name;
```

- OpenMetadata에 수집할 관련 테이블에 대해 사용자에게 `GRANT SELECT` 권한이 필요합니다.
```sql
GRANT SELECT ON table_name TO user_name;
```

### Profiler & Data Quality
Profiler 워크플로우 또는 데이터 품질 테스트를 실행하려면, profiler/테스트가 실행될 테이블/스키마에 대해 사용자가 `SELECT` 권한을 가져야 합니다. Profiler 워크플로우 설정에 대한 자세한 내용은 [여기](https://docs.open-metadata.org/how-to-guides/data-quality-observability/profiler/workflow)에서, 데이터 품질 테스트에 대한 내용은 [여기](https://docs.open-metadata.org/connectors/ingestion/workflows/data-quality)에서 확인할 수 있습니다.

### Usage & Lineage
Usage 및 Lineage 워크플로우의 경우, 사용자에게 `SELECT` 권한이 필요합니다. Usage 워크플로우에 대한 자세한 내용은 [여기](https://docs.open-metadata.org/connectors/ingestion/workflows/usage)에서, Lineage 워크플로우에 대한 내용은 [여기](https://docs.open-metadata.org/connectors/ingestion/workflows/lineage)에서 확인할 수 있습니다.

## 연결 세부 정보

$$section
### Scheme $(id="scheme")

**tibero+pyodbc**: Tibero에 연결하기 위한 SQLAlchemy 스키마입니다.
$$

$$section
### Username $(id="username")

Tibero에 연결하기 위한 사용자 이름입니다. 이 사용자는 Tibero의 모든 메타데이터를 읽을 수 있는 권한을 가져야 합니다.
$$

$$section
### Password $(id="password")

Tibero에 연결하기 위한 비밀번호입니다.
$$

$$section
### Host Port $(id="hostPort")

이 매개변수는 Tibero 인스턴스의 호스트와 포트를 지정합니다. `hostname:port` 형식의 문자열로 지정해야 합니다. 예를 들어, hostPort 매개변수를 `localhost:8629`로 설정할 수 있습니다.

OpenMetadata ingestion을 Docker에서 실행하고 서비스가 `localhost`에서 호스팅되는 경우, 값으로 `host.docker.internal:8629`를 사용하세요.
ex. `172.17.0.1:8629`
$$

$$section
### Database Name $(id="databaseName")

Tibero에서 연결할 데이터베이스의 이름입니다.
$$

$$section
### Driver $(id="driver")

Tibero용 ODBC 드라이버 이름입니다. 기본값은 `Tibero7Driver`입니다.
$$

$$section
### Connection Options $(id="connectionOptions")

연결 중에 Tibero로 전송할 수 있는 추가 연결 옵션의 세부 정보를 입력하세요. 이러한 세부 정보는 Key-Value 쌍으로 추가해야 합니다.
$$

$$section
### Connection Arguments $(id="connectionArguments")

연결 중에 Tibero로 전송할 수 있는 보안 또는 프로토콜 구성과 같은 추가 연결 인수의 세부 정보를 입력하세요. 이러한 세부 정보는 Key-Value 쌍으로 추가해야 합니다.
$$

