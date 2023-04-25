# Streaming-Pipeline
The purpose of this project was to create and end-to-end streaming pipeline of near-realtime GPS data of local transit (TTC) streetcar locations to enable route optimization

## Data Ingestion
1. Apache Nifi was deployed on an AWS EC2 instance to poll a public data source via REST API, and tabulate the JSON response objects into a MySQL database deployed on the same instance
2. Debezium CDC was set up to capture the changes (CDC) to the MySQL database and feed those changes into Kafka

## Data Transformation
1. AWS MSK was the choice of Kafka deployment for event handling, taking the new data and feeding it into a Spark Streaming job
2. An AWS EMR cluster ran the Spark Streaming job of extracting only the useful data and dumping it into an Apache Hudi table located in S3

## Data Analysis
1. AWS Glue crawler accesses the Hudi table and Athena was the Query engine running in tandem with Glue
2. PowerBI's ArcGIS plugin was used to visualize the data to show the slowest and fastest portions of the route

## Architecture Diagram
![Alt text](https://github.com/Alex-J-Hill/Streaming-Pipeline/blob/main/ArchitectureDiagram.png "Architecture Diagram")
