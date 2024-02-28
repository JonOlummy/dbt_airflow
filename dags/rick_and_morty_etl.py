from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import Mount
sys.path.append('/opt/airflow')

from scripts.rick_morty_api_load import fetch_characters, fetch_locations, define_schema_and_tables, insert_character_data, insert_location_data

#define the dag
default_args = {
    'owner': 'raft_airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 2, 28),
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

dag = DAG(
    'rick_and_morty_etl',
    default_args=default_args,
    description='ETL data pipeline for Rick and Morty API',
    schedule_interval=timedelta(days=1),
)



define_schema_task = PythonOperator(
    task_id='define_schema_and_tables',
    python_callable=define_schema_and_tables,
    dag=dag,
)

fetch_characters_task = PythonOperator(
    task_id='fetch_characters_task',
    python_callable=fetch_characters,
    dag=dag,
)

insert_characters_task = PythonOperator(
    task_id='insert_characters_task',
    python_callable=insert_character_data,
    dag=dag,
)

fetch_locations_task = PythonOperator(
    task_id='fetch_locations_task',
    python_callable=fetch_locations,
    dag=dag,
)

insert_locations_task = PythonOperator(
    task_id='insert_locations_task',
    python_callable=insert_location_data,
    dag=dag,
)

run_dbt = DockerOperator(
    task_id='dbt_run',
    image='raft_airflow-dbt_tool',
    api_version='auto',
    auto_remove=True,
    command='dbt run --models location_character_merge',
    docker_url="tcp://docker-proxy:2375",
    network_mode='bridge',
    mounts=[Mount(source="./dbt", target="/opt/airflow/dbt", type="bind")],
    mount_tmp_dir=False,
    dag=dag,
)

define_schema_task >> fetch_characters_task >> insert_characters_task >> fetch_locations_task >> insert_locations_task >> run_dbt