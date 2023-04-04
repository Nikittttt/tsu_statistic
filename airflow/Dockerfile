ARG AIRFLOW_IMAGE

FROM $AIRFLOW_IMAGE
COPY requirements.txt .
USER airflow
RUN pip install --no-cache-dir --user -q -r requirements.txt