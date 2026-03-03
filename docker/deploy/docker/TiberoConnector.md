
# Tibero Connector Guide

이 문서는 Tibero Connector를 사용하여 OpenMetadata에서 Metadata를 수집하고, Profiler, Lineage 등을 구성하는 방법을 안내합니다.  

---

## Feature List

| Feature | 지원 여부 |
|----------|-----------|
| Metadata | ✅ |
| Data Profiler | ✅ |
| dbt | ✅ |
| Lineage | ✅ |
| Column-level Lineage | ✅ |
| Stored Procedures | ✅ |
| Sample Data | ✅ |
| Auto-Classification | ✅ |

---

## Requirements

**Note**  
Tibero Database에서 Metadata를 수집하기 위해 `pyodbc+tibero` 라이브러리를 사용합니다.  
이 라이브러리는 Tibero 7 버전을 지원합니다.

Metadata를 수집하기 위해서는 **CREATE SESSION** 권한이 필요합니다.

```sql
-- CREATE USER
CREATE USER user_name IDENTIFIED BY admin_password;

-- CREATE ROLE
CREATE ROLE new_role;

-- GRANT ROLE TO USER
GRANT new_role TO user_name;

-- GRANT CREATE SESSION TO new_role;
--    Data Dictionary를 ReadOnly로 조회할 수 있는 권한
GRANT SELECT_CATALOG_ROLE TO new_role;
```

**Note**  
위의 권한만으로 Metadata 수집은 가능하지만,  
**Profiler** 기능을 사용하려면  
수집 대상 테이블에 **SELECT 권한**을 추가로 부여해야 합니다.

```sql
-- Role을 사용 중이며 특정 테이블 지정 없이 모든 테이블 SELECT 허용
GRANT SELECT ANY TABLE TO new_role;

-- Role 없이 사용자에게 직접 모든 테이블 SELECT 허용
GRANT SELECT ANY TABLE TO my_user;

-- Role 사용 시 특정 테이블에 권한 부여
GRANT SELECT ON ADMIN.EXAMPLE_TABLE TO new_role;

-- 사용자에게 직접 특정 테이블에 권한 부여
GRANT SELECT ON ADMIN.EXAMPLE_TABLE TO my_user;

-- Role 사용 시 스키마/테이블 지정
GRANT SELECT ON {schema}.{table} TO new_role;

-- 사용자에게 직접 스키마/테이블 지정
GRANT SELECT ON {schema}.{table} TO my_user;
```


## Metadata Ingestion

### 1. Services 페이지로 이동

사이드바에서 **Settings → Services**를 클릭합니다.

Metadata를 수집하기 위해서는 먼저 **Service Connection**을 생성해야 합니다.  
이 Service는 OpenMetadata와 데이터 소스 간의 연결 다리 역할을 합니다.

Service를 한 번 생성하면 여러 Ingestion Workflow에서 재사용할 수 있습니다.

---

### 2. 새 Service 생성

**Add New Service** 버튼을 클릭하여 새 Service 생성을 시작합니다.

---

### 3. Service Type 선택

Service Type으로 **Tibero**를 선택하고 **Next**를 클릭합니다.

---

### 4. Service 이름 및 설명 입력

Service 이름과 설명을 입력합니다.

**Service Name**  
OpenMetadata는 Service Name으로 Service를 고유하게 식별합니다.  
다른 Oracle Service나 다른 커넥터와 구분되는 이름을 입력하세요.  
한 번 설정된 Service Name은 변경할 수 없습니다.

---

### 5. Service Connection 구성

이 단계에서는 Tibero와 연결하기 위한 Connection 설정을 구성합니다.  
오른쪽 패널에서 연결 설정에 대한 가이드를 참고할 수 있습니다.

#### Connection Details

- **Username** : Tibero에 연결할 사용자 이름을 입력합니다. Metadata를 조회할 수 있는 권한이 필요합니다.  
- **Password** : Tibero 사용자 비밀번호를 입력합니다.  
- **Host and Port** : Tibero 인스턴스의 호스트명과 포트를 입력합니다.  

  **Database Name (선택사항)**  
  OpenMetadata 내에서 사용할 Database 이름을 입력합니다.  
  비워두면 기본값이 사용됩니다.  
  Database 이름을 **SID와 동일하게 설정하는 것을 권장**합니다.  
  이렇게 하면 Profiling, Data Quality, dbt Workflow 등에서 정확한 매칭이 가능합니다.



---

### Advanced Configuration

고급 설정을 통해 추가적인 Connection 옵션을 전달하거나 Connection Scheme을 수정할 수 있습니다.  
보통은 기본값으로 충분하지만, 보안/네트워크 옵션이 필요한 경우 활용합니다.

- **Connection Options (Optional)** :  
  Key-Value 형태의 추가 Connection 옵션.
- **Connection Arguments (Optional)** :  
  보안 또는 프로토콜 관련 설정 값. 역시 Key-Value 형태로 입력.

tibero ssl 설정의 경우에는 [통신 암호화](https://technet.tmax.co.kr/upload/download/online/tibero/pver-20240502-000002/tibero_admin/chapter_ssl.html) 를 참고 부탁 드립니다.  

---

### 6. Test Connection

모든 Connection 정보를 입력한 뒤 **Test Connection**을 클릭하여 연결을 확인합니다.  
정상적으로 연결이 완료되면 **Save Changes**를 클릭합니다.

---

### 7. Metadata Ingestion 설정

이 단계에서는 Metadata Ingestion Pipeline을 구성합니다.

#### Metadata Ingestion Options

> 만약 Owner 이름이 `openmetadata`라면,  
> **Add Team/User** 폼의 이름란에 `openmetadata@domain.com`을 입력해야 합니다.

- **Name** : Ingestion Pipeline의 이름. 자동 생성된 이름을 그대로 사용하거나 직접 지정할 수 있습니다.  
- **Database Filter Pattern (Optional)**  
  Database 이름을 기준으로 포함/제외할 항목을 지정합니다.  
  - Include : 정규식 목록 중 하나라도 일치하면 포함.  
  - Exclude : 정규식 목록 중 하나라도 일치하면 제외.  
- **Schema Filter Pattern (Optional)**  
  스키마(유저) 이름을 기준으로 포함/제외할 항목을 지정합니다.  
  Include/Exclude 규칙은 Database Filter Pattern과 동일합니다.  
  필터는 대소문자를 구분합니다.  
- **Table Filter Pattern (Optional)**  
  테이블 이름을 기준으로 포함/제외할 항목을 지정합니다.  
  필터는 대소문자를 구분합니다.  
- **Enable Debug Log (toggle)**  
  기본 로그 레벨을 debug로 설정합니다.  
- **Mark Deleted Tables (toggle)**  
  더 이상 존재하지 않는 테이블을 Soft Delete로 표시합니다.  
- **Mark Deleted Tables from Filter Only (toggle)**  
  Filter에 포함된 Database/Schema 내에서만 삭제 감지를 수행합니다.  
  여러 Ingestion Pipeline을 병행할 때 유용합니다.  
- **includeTables (toggle)**  
  테이블 Metadata 수집 여부를 설정합니다.  
- **includeViews (toggle)**  
  View Metadata 수집 여부를 설정합니다.  
- **includeTags (toggle)**  
  Tag 정보를 포함할지 여부를 설정합니다.  
- **includeOwners (toggle)**  
  Owner 정보를 포함할지 여부를 설정합니다.  
  Owner Email이 OpenMetadata 서버에 등록된 User와 일치할 경우 자동 매핑됩니다.  
  이미 Owner가 지정된 Entity는 덮어쓰지 않습니다.  
- **includeStoredProcedures (toggle)**  
  Stored Procedure Metadata를 포함할지 여부를 설정합니다.  
- **includeDDL (toggle)**  
  DDL Statement 수집 여부를 설정합니다.  
- **queryLogDuration (Optional)**  
  Stored Procedure 결과를 수집할 때 조회할 Query Log의 기간(일 단위).  
- **queryParsingTimeoutLimit (Optional)**  
  쿼리 파싱 제한 시간(초 단위).  
- **useFqnForFiltering (toggle)**  
  Filter 정규식을 FQN(`service.db.schema.table`) 기준으로 적용할지 여부를 설정합니다.  
- **Incremental (Beta)**  
  첫 실행 이후 변경된 Metadata만 추출하는 Incremental Extraction을 활성화합니다.  
  (현재 BigQuery, Redshift, Snowflake에서만 지원)  
  - Enabled : Incremental 모드 활성화 여부  
  - lookback Days : 최근 성공한 Pipeline 실행 시점을 기준으로 검색할 기간  
  - Safety Margin Days : 추가 보정 기간(일 단위)  
- **Threads (Beta)**  
  Metadata Extraction을 병렬로 수행할 스레드 개수를 설정합니다.  
  자세한 내용은 *Metadata Ingestion - Multithreading* 문서를 참고하세요.  

> 오른쪽 패널에는 각 설정 항목에 대한 도움말이 표시됩니다.

---

### 8. Schedule & Deploy

Ingestion 스케줄을 설정합니다.  
스케줄은 **Hourly / Daily / Weekly / Manual** 중 선택 가능하며,  
시간대(Timezone)는 UTC 기준입니다.

시작일(Start Date)과 종료일(End Date)을 선택할 수 있습니다.

모든 설정을 검토한 뒤 문제가 없으면 **Deploy**를 클릭하여  
Service 생성 및 Ingestion Pipeline 배포를 완료합니다.

---

### 9. Ingestion Pipeline 확인

Workflow가 성공적으로 배포되면  
Service 페이지에서 해당 Ingestion Pipeline의 상태를 확인할 수 있습니다.

---


### Related

- [Usage Workflow](https://docs.open-metadata.org/latest/connectors/ingestion/workflows/usage)  
- [Lineage Workflow](https://docs.open-metadata.org/latest/connectors/ingestion/workflows/lineage)  
- [Profiler Workflow](https://docs.open-metadata.org/latest/how-to-guides/data-quality-observability/profiler/workflow)  
- [Data Quality Workflow](https://docs.open-metadata.org/latest/how-to-guides/data-quality-observability/quality/configure)  
- [dbt Integration](https://docs.open-metadata.org/latest/connectors/ingestion/workflows/dbt)

---



