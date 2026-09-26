FROM apache/airflow:3.3.2-python3.12

USER airflow

COPY pyproject.toml README.md /opt/insightfuel/
COPY src /opt/insightfuel/src

RUN pip install --no-cache-dir /opt/insightfuel