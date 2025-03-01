# cryptocurrency-ETLPipeline-Airflow

 This project utilized Apache Airflow to manage the workflow of an ETL pipeline used to extract cryptocurrency data from [coincap](www.coincap.com), transform the data, and load the transformed data to a Postgres database.

 ## Folders Description

 There are three folders in this repository. 
 The **config** folder holds configuration files and any external file to serve as input in the DAGS. 
 The **dags** folder contains DAG files written in python. The *crypto_coins_dag.py* is the main DAG file for this project and can be found in the dags folder. 
 The **logs** folder contains the log information for the DAGS. Each log of the DAG is identified by the dag id. 
 The **docker-compose.yaml** is the docker file used to set up Apache Airflow to manage the workflow.
