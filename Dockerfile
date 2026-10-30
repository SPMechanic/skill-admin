# Dev container for running skill-admin tests in a clean environment.
# Usage:
#   docker build -t skill-admin-test .
#   docker run --rm -v %USERPROFILE%\.skill-admin:/root/.skill-admin skill-admin-test

FROM python:3.15-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir pytest

CMD ["pytest", \
     "tests/test_catalog_db.py", \
     "tests/test_recommend_engine.py", \
     "tests/test_catalog_freshness.py", \
     "tests/test_plugin_manifest.py", \
     "tests/test_repo_structure.py", \
     "-q"]
