# Import libraries
from airflow.models import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.utils.dates import days_ago
from datetime import timedelta
import pandas as pd
from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json

def extract(ti):
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
    parameters = {
    'start':'1',
    'limit':'200',
    'convert':'USD'
    }
    headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': '38833fee-5ef1-4902-87f0-7e3c98da7327',
    }

    session = Session()
    session.headers.update(headers)

    try:
        response = session.get(url, params=parameters)
        data = json.loads(response.text)
        ti.xcom_push(key="crypto_data", value=data)
        print("Cryptocurrencies data extracted successfully")
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        print(e)

def transform(ti):
    data = ti.xcom_pull(key="crypto_data", task_ids='fetch_crypto_data')
    crypto_list = []
    for crypto in data["data"]:
        dict_ = {
            "id": crypto["id"],
            "Name": crypto["name"],
            "Symbol": crypto["symbol"],
            "Price": round(crypto["quote"]["USD"]["price"], 2),
            "24h Percent Change": round(crypto["quote"]["USD"]["percent_change_24h"], 2),
            "7d Percent Change": round(crypto["quote"]["USD"]["percent_change_7d"], 2),
            "30d Percent Change": round(crypto["quote"]["USD"]["percent_change_30d"], 2),
            "Market Cap": round(crypto["quote"]["USD"]["market_cap"], 2),
            "Circulating Supply": crypto["circulating_supply"]       
        }
        crypto_list.append(dict_)

    df = pd.DataFrame(crypto_list)
    ti.xcom_push(key="dataframe", value=df.to_dict('records'))

def insert_data_into_postgres(ti):
    coin_data = ti.xcom_pull(key='dataframe', task_ids='parse_coin_data')
    if not coin_data:
        raise ValueError("No data found")
    #hooks - allows connection to postgres
    postgres_hook = PostgresHook(postgres_conn_id='Cryptocurrencies_connection')
    insert_query = """
    INSERT INTO coins_data (id, name, symbol, price, percent_change_24h, percent_change_7d, percent_change_30d, market_cap, circulating_supply)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    for coin in coin_data:
        postgres_hook.run(insert_query, parameters=(coin["id"], coin["Name"], coin["Symbol"], coin["Price"], coin["24h Percent Change"], coin["7d Percent Change"], coin["30d Percent Change"], coin["Market Cap"], coin["Circulating Supply"]))


default_args = {
    'owner': 'Akinkunmi',
    'start_date': days_ago(0),
    'email': ['olalekanrasaq1331@gmail.com'],
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'fetch_cryptocurrencies_data',
    default_args=default_args,
    description='A DAG to fetch cryptocurrencies data from CoinMarketCap and store it in Postgres',
    schedule_interval=timedelta(days=1),
)

#operators : Python Operator and PostgresOperator


fetch_crypto_data = PythonOperator(
    task_id='fetch_crypto_data',
    python_callable=extract,
    dag=dag,
)

parse_data = PythonOperator(
    task_id='parse_coin_data',
    python_callable=transform,
    dag=dag,
)

create_table_task = PostgresOperator(
    task_id='create_table',
    postgres_conn_id='Cryptocurrencies_connection',
    sql="""
    CREATE TABLE IF NOT EXISTS coins_data (
        id INT,
        name TEXT NOT NULL,
        symbol TEXT,
        price NUMERIC(12,2),
        percent_change_24h NUMERIC(6,2),
        percent_change_7d NUMERIC(6,2),
        percent_change_30d NUMERIC(6,2),
        market_cap NUMERIC(20,2),
        circulating_supply BIGINT
    );
    """,
    dag=dag,
)

insert_coin_data_task = PythonOperator(
    task_id='insert_coin_data_postgres',
    python_callable=insert_data_into_postgres,
    dag=dag,
)

# Task pipeline

fetch_crypto_data >> parse_data >> create_table_task >> insert_coin_data_task