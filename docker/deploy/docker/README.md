# OpenMetadata-Tibero Docker Deployment Guide

## 개요  
본 문서는 **OpenMetadata Server(서버) 및 Ingestion(수집기) 컨테이너**를 Docker Compose를 통해 배포하는 방법을 설명합니다.  
Tibero 커넥터가 포함된 커스텀 이미지를 기준으로 작성되었으며,  
커스텀 이미지는 OpenMetadata 1.9.11 ingestion, server 이미지를 통해 빌드 하였습니다.  
외부 **MySQL / PostgreSQL / ElasticSearch** 서비스를 미리 준비해야 합니다(권장).  
Quickstart 방식으로 Docker Compose 실행 시, PostgreSQL과 ElasticSearch 컨테이너가 같이 실행 됩니다.  


자세한 내용은 공식 문서를 참고하세요.  
👉 [OpenMetadata 공식 Docker 배포 가이드](https://docs.open-metadata.org/latest/deployment/docker)

---

## 요구사항  

- Docker 20.10.0 이상  
- Docker Compose v2.2.3 이상  
- MySQL 8.x 이상 또는 PostgreSQL 12.x 이상  
- ElasticSearch 8.x 이상 ~ 8.11.4 이하 (권장)  
- Python 3.10 이상 (Ingestion 내부 엔진용)

> **참고:** Production 환경에서는 Quickstart 이미지를 사용하지 않고,  
> 외부 Database 및 ElasticSearch를 직접 구성하는 것을 권장합니다.  

---

## Docker 이미지 준비  

`openmetadata-tibero-images.tar` 파일에는 다음 이미지가 포함되어 있습니다.  
- `openmetadata/server`  
- `openmetadata/ingestion`  

압축 해제 및 로드 명령어 예시:

```bash
docker load -i openmetadata-tibero-images.tar
docker images | grep openmetadata  
```

이미지가 정상적으로 로드되면, Server와 Ingestion 이미지가 목록에 표시됩니다.

---

## Docker Compose 파일 구성  

`openmetadata-tibero.tar` 파일을 해제하면 다음 구조로 되어 있습니다.

```text
docker/
├─ docker-compose-openmetadata/
│ ├─ docker-compose-openmetadata-custom.yml
│ ├─ env-mysql
│ └─ env-postgresql
├─ docker-compose-ingestion/
│ ├─ docker-compose-ingestion-custom.yml
│ ├─ env-mysql
│ └─ env-postgresql
├─ docker-compose-quickstart/
│ ├─ docker-compose-postgres-custom.yml
│ └─ env
├─ openmetadata-tibero-server.tar
└─ openmetadata-tibero-ingestion.tar
```


두 Compose 파일은 동일한 Docker 네트워크(`omd_net`)에서 실행되어야 하며,  
외부 DB 및 ElasticSearch 컨테이너도 같은 네트워크에 포함되어야 합니다.
Quickstart의 경우 별도 설정 없이도 같은 네트워크에서 실행됩니다.  

예시:
```
docker network connect omd_net mysql  
docker network connect omd_net elasticsearch  
```

> 동일한 `subnet` 대역을 사용하는 다른 네트워크가 있을 경우,  
> `172.16.240.0/24` 값을 변경해야 합니다.

---

## 실행 및 종료  

최초 실행 시 docker compose yaml 파일에 컨테이너 생성을 위한 기본 값이 yaml 파일에 세팅 되어 있으며,  
실행 시 -f 옵션으로 yaml 파일 (`docker-compose-openmetadata-custom.yml`, `docker-compose-ingestion-custom.yml`)을 지정해야 합니다.  
quickstart 시에는 `docker-compose-postgres-custom.yml`로 지정해야 합니다.
환경 변수를 원하는 값으로 세팅하려면  
환경변수 파일(`env-mysql` 또는 `env-postgresql`)을 지정해야 합니다.  

최초 실행 명령:  
```bash
// 최초 실행 시
docker compose -f <yml 파일> up -d

// 환경 변수 설정 시
docker compose -f <yml 파일> --env-file <env 파일> up -d  
```

중지 및 재시작 명령:  
```bash
// 컨테이너 중지
docker compose -f <yml 파일> --env-file <env 파일> stop

// 컨테이너 재시작
docker compose -f <yml 파일> --env-file <env 파일> start

// 컨테이너 완전 종료 및 삭제
docker compose -f <yml 파일> --env-file <env 파일> down
```
로그 확인:  
```bash
docker logs -f openmetadata_server  
docker logs -f ingestion  
```

---

## 주요 환경 변수  

### MySQL  
```text
DB_DRIVER_CLASS=com.mysql.cj.jdbc.Driver  
DB_SCHEME=mysql  
DB_USER=openmetadata_user  
DB_USER_PASSWORD=openmetadata_password  
DB_HOST=mysql  
DB_PORT=3306  
OM_DATABASE=openmetadata_db  
```

### ElasticSearch  
```text
SEARCH_TYPE=elasticsearch  
ELASTICSEARCH_HOST=elasticsearch  
ELASTICSEARCH_PORT=9200  
ELASTICSEARCH_SCHEME=http  
```

### Ingestion (Airflow)  
```text
PIPELINE_SERVICE_CLIENT_ENDPOINT=http://airflow:8080  
SERVER_HOST_API_URL=http://openmetadata_server:8585/api  
AIRFLOW_USERNAME=admin  
AIRFLOW_PASSWORD=admin  
```

> HTTPS 환경에서는 `ELASTICSEARCH_SCHEME=https` 로 변경하고  
> `ELASTICSEARCH_USER`, `ELASTICSEARCH_PASSWORD`를 지정해야 합니다.

---

## 기본 계정 정보  

**OpenMetadata UI**  
- 주소: http://localhost:8585  
- ID: admin@open-metadata.org  
- PW: admin  

**Airflow UI**  
- 주소: http://localhost:8080  
- ID: admin  
- PW: admin  

> 배포 후 반드시 관리자 계정 비밀번호를 변경하세요.

---

## 이후 실행

일반 계정 생성 시 수집(ingestion) 권한이 없습니다.
admin 계정에서 

## Troubleshooting  

**메모리 부족 오류 (OutOfMemoryError)**  
- env 파일에 다음 설정 추가 후 재시작  
  OPENMETADATA_HEAP_OPTS="-Xmx2G -Xms2G"

**네트워크 충돌 시**  
- subnet이 중복된다면 `172.18.0.0/24` 등으로 변경 후 다시 실행  

---

## 참고 문서  

- [OpenMetadata Deployment Guide](https://docs.open-metadata.org/latest/deployment/docker)  
- [Minimum Requirements](https://docs.open-metadata.org/latest/deployment/minimum-requirements)  
- [Docker Compose Reference](https://docs.docker.com/compose/)

---

_Last Updated: 2025-11-07_  
_Author: Tibero Client Interface Team_

