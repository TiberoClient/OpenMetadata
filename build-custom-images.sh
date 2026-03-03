#!/bin/bash
#  Copyright 2021 Collate
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#  http://www.apache.org/licenses/LICENSE-2.0
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

# OpenMetadata Custom Images Builder
# Tibero 커넥터가 포함된 Server 및 Ingestion 이미지 빌드

set -e

VERSION="1.9.11"
CUSTOM_TAG="${VERSION}-tibero"

echo "=========================================="
echo "OpenMetadata Custom Images Builder"
echo "Version: ${VERSION}"
echo "Custom Tag: ${CUSTOM_TAG}"
echo "=========================================="

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 함수: 단계 출력
step() {
    echo -e "\n${GREEN}[STEP]${NC} $1"
}

# 함수: 경고 출력
warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# 함수: 에러 출력
error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 1. Maven 빌드
step "1. Building Maven packages (Backend + UI)"
if [ ! -f "openmetadata-dist/target/openmetadata-${VERSION}.tar.gz" ]; then
    echo "Building with Maven (including UI)..."
    mvn clean package -DskipTests || {
        error "Maven build failed!"
        exit 1
    }
else
    warn "tar.gz already exists. Skipping Maven build. (Use 'rm -rf openmetadata-dist/target' to force rebuild)"
fi

# 2. Server 이미지 빌드
step "2. Building Server Image (openmetadata-server-custom:${CUSTOM_TAG})"
docker build -f Dockerfile.server-overlay -t openmetadata-server-custom:${CUSTOM_TAG} . || {
    error "Server image build failed!"
    exit 1
}

echo -e "${GREEN}✓${NC} Server image built successfully: openmetadata-server-custom:${CUSTOM_TAG}"

# 3. Ingestion 이미지 빌드
step "3. Building Ingestion Image (openmetadata-ingestion-custom:${CUSTOM_TAG})"
docker build -f Dockerfile.ingestion-overlay -t openmetadata-ingestion-custom:${CUSTOM_TAG} . || {
    error "Ingestion image build failed!"
    exit 1
}

echo -e "${GREEN}✓${NC} Ingestion image built successfully: openmetadata-ingestion-custom:${CUSTOM_TAG}"

# 4. 빌드 결과 출력
step "4. Build Summary"
echo ""
echo "=========================================="
echo "Build completed successfully! 🎉"
echo "=========================================="
echo ""
echo "Built images:"
echo "  1. openmetadata-server-custom:${CUSTOM_TAG}"
echo "  2. openmetadata-ingestion-custom:${CUSTOM_TAG}"
echo ""
echo "Image sizes:"
docker images | grep -E "REPOSITORY|openmetadata-.*-custom" | grep -E "REPOSITORY|${CUSTOM_TAG}"
echo ""
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Test images:"
echo "     docker run --rm openmetadata-server-custom:${CUSTOM_TAG} --version"
echo ""
echo "  2. Tag for registry (optional):"
echo "     docker tag openmetadata-server-custom:${CUSTOM_TAG} YOUR_REGISTRY/openmetadata-server:${CUSTOM_TAG}"
echo "     docker tag openmetadata-ingestion-custom:${CUSTOM_TAG} YOUR_REGISTRY/openmetadata-ingestion:${CUSTOM_TAG}"
echo ""
echo "  3. Push to registry (optional):"
echo "     docker push YOUR_REGISTRY/openmetadata-server:${CUSTOM_TAG}"
echo "     docker push YOUR_REGISTRY/openmetadata-ingestion:${CUSTOM_TAG}"
echo ""
echo "  4. Use with docker-compose:"
echo "     Update docker-compose.yml with custom image names"
echo ""
echo "=========================================="

