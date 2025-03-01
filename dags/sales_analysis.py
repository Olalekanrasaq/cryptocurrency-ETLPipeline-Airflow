# Import libraries
from airflow.models import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from datetime import timedelta
import pandas as pd


def read_file(ti):
    input_file = "/opt/airflow/config/sales_data.csv"
    df = pd.read_csv(input_file)
    
    # Push the DataFrame (converted to dict) to XCom
    ti.xcom_push(key='dataframe', value=df.to_dict())
    print("CSV file read successfully.")

def transform(ti):
    data = ti.xcom_pull(key="dataframe", task_ids='read_file')
    df = pd.DataFrame(data)
    df["Sales Price"] = df["unit price"] * df["Order qty"]
    df["Cost Price"] = df["unit cost"] * df["Order qty"]
    df["Profit"] = df["Sales Price"] - df["Cost Price"]

    ti.xcom_push(key='transformed_df', value=df.to_dict())

def load_file(ti):
    output_file = "/opt/airflow/config/cleaned_sales_data.csv"
    data = ti.xcom_pull(key='transformed_df', task_ids="transform")
    df = pd.DataFrame(data)
    df.to_csv(output_file, index=False)

# default arguments
default_args = {
    'owner': 'Akinkunmi',
    'start_date': days_ago(0),
    'email': ['olalekanrasaq1331@gmail.com'],
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG
dag = DAG(
    'sales-analysis-dag',
    default_args=default_args,
    description='Analysis of Sales data',
    schedule_interval=timedelta(days=1),
)

# Define the tasks
read_csv_file = PythonOperator(
    task_id='read_file',
    python_callable=read_file,
    dag=dag,
)

transform_file = PythonOperator(
    task_id='transform',
    python_callable=transform,
    dag=dag,
)

load_output = PythonOperator(
    task_id='save_transformed_file',
    python_callable=load_file,
    dag=dag,
)

# Task pipeline
read_csv_file >> transform_file >> load_output