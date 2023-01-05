from pyspark.sql import SparkSession
from pyspark.sql.types import *
from pyspark.sql.functions import *

# NOTE: This variable needs to be reviewed if we are working with a new MSK
BOOTSTRAP_SERVERS = "b-3.finalproject2.9g6hr3.c20.kafka.us-east-1.amazonaws.com:9092,b-2.finalproject2.9g6hr3.c20.kafka.us-east-1.amazonaws.com:9092,b-1.finalproject2.9g6hr3.c20.kafka.us-east-1.amazonaws.com:9092"

if __name__ == "__main__":
    spark = SparkSession.builder.getOrCreate()

    # NOTE: we cant load the schema file from the local machine anymore, so we have to pull it from s3
    schema = spark.read.json(
        #"s3://bus-service-wcd-eu-west-1/msk/bus_status_schema.json"
        "s3://wcdfinalajh/bus_status_schema.json"
    ).schema
    print(schema)

    # We have to connect to the bootstrap servers, instead of kafka:9092
    df = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", BOOTSTRAP_SERVERS)
        .option("subscribe", "dbserver1.demo.bus_status")
        .option("startingOffsets", "latest")
        .load()
    )

    transform_df = (
        df.select(col("value").cast("string"))
        .alias("value")
        .withColumn("jsonData", from_json(col("value"), schema))
        .select("jsonData.payload.after.*")
    )

    # NOTE: We cannot checkpoint to a local machine because we are working on the cloud. S3 is a reliable location for the cluster
    # checkpoint_location = "s3://bus-service-wcd-eu-west-1/msk/checkpoint/sparkjob"
    checkpoint_location = "s3://wcdfinalajh/checkpoint"

    table_name = "bus_status"
    hudi_options = {
        "hoodie.table.name": table_name,
        "hoodie.datasource.write.table.type": "COPY_ON_WRITE",
        "hoodie.datasource.write.recordkey.field": "record_id",
        "hoodie.datasource.write.partitionpath.field": "routeId",
        "hoodie.datasource.write.table.name": table_name,
        "hoodie.datasource.write.operation": "upsert",
        "hoodie.datasource.write.precombine.field": "event_time",
        "hoodie.upsert.shuffle.parallelism": 100,
        "hoodie.insert.shuffle.parallelism": 100,
    }

    s3_path = "s3://wcdfinalajh/routes2/"

    def write_batch(batch_df, batch_id):
        batch_df.write.format("org.apache.hudi").options(**hudi_options).mode(
            "append"
        ).save(s3_path)

    transform_df.writeStream.option(
        "checkpointLocation", checkpoint_location
    ).queryName("wcd-bus-streaming").foreachBatch(
        write_batch
    ).start().awaitTermination()
