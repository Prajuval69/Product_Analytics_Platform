FROM apache/airflow:2.10.5-python3.11
USER root
RUN mkdir -p /opt/platform /opt/analytics-venv && chown -R airflow:root /opt/platform /opt/analytics-venv
USER airflow
RUN pip install --no-cache-dir pytest==8.3.5
COPY --chown=airflow:root . /opt/platform
RUN umask 0002; mkdir -p /opt/platform/dbt/target /opt/platform/dbt/logs \
    && python -m venv /opt/analytics-venv \
    && /opt/analytics-venv/bin/pip install --no-cache-dir -r /opt/platform/requirements.lock \
    && /opt/analytics-venv/bin/pip install --no-cache-dir --no-deps -e /opt/platform
ENV PYTHONUNBUFFERED=1
