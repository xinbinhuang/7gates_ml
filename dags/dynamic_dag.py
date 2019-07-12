"""
A dynamic generated DAG

Note: Use DAG docstring to link design documentations, dependencies etc. 
"""
import json
import os
from pathlib import Path

from airflow import utils
from airflow.models import DAG
from datetime import datetime, timedelta
from airflow.operators.dummy_operator import DummyOperator


AIRFLOW_HOME=os.environ['AIRFLOW_HOME']


def create_dag(dag_id,
               schedule,
               default_args,
               conf):
    dag = DAG(dag_id, default_args=default_args, schedule_interval=schedule)
    with dag:
        init = DummyOperator(
            task_id='Init',
            dag=dag
        )
        extract = DummyOperator(
            task_id='extract',
            dag=dag
        )
        load = DummyOperator(
            task_id='load',
            dag=dag
        )

        transform_internal_tables = [DummyOperator(
            task_id=f'transform_{table}',
            dag=dag) 
            for table in conf['tables']]
        
        extract_side_intput = DummyOperator(
            task_id='extract_side_input',
            dag=dag
        )

        external_tables = [DummyOperator(
            task_id=f'transform_side_input_{source}',
            dag=dag) 
            for source in conf['external']]

        init >> extract >> transform_internal_tables
        extract_side_intput >> external_tables
        (transform_internal_tables + external_tables) >> load
        return dag


with (Path(AIRFLOW_HOME) / 'config' / 'pipeline_config.json').open() as json_data:
    conf = json.load(json_data)
    schedule = conf['schedule']
    dag_id = conf['name']
    args = {
        'owner': 'dynamic_dag_from_json',
        'description': 'Dynamic Dag from json config',
        'depends_on_past': False,
        'start_date': utils.dates.days_ago(3),
        'email': ['example@gmail.com'],
        'email_on_failure': False,
        'email_on_retry': False,
        'retries': 1,
        'retry_delay': timedelta(minutes=5),
        'max_active_runs': 3
    }

    for i in range(5):
        dag_id = f'dynamic_{i}'
        globals()[dag_id] = create_dag(dag_id, schedule, args, conf)
