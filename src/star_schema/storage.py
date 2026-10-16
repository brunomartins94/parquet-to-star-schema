from __future__ import annotations

import io
from datetime import date

import boto3
import pyarrow as pa
import pyarrow.parquet as pq
from botocore.exceptions import ClientError


class S3ModelStore:
    def __init__(self, source_bucket: str, target_bucket: str, region: str) -> None:
        self.source_bucket = source_bucket
        self.target_bucket = target_bucket
        self.client = boto3.client("s3", region_name=region)

    @staticmethod
    def source_key(prefix: str, ingested_on: date) -> str:
        return f"{prefix}/ingested_date={ingested_on.isoformat()}/breweries.parquet"

    @staticmethod
    def model_key(prefix: str, ingested_on: date, model_name: str) -> str:
        return f"{prefix}/ingested_date={ingested_on.isoformat()}/{model_name}.parquet"

    def read_source(self, key: str) -> pa.Table:
        response = self.client.get_object(Bucket=self.source_bucket, Key=key)
        return pq.read_table(pa.BufferReader(response["Body"].read()))

    def write_if_missing(self, key: str, table: pa.Table) -> bool:
        try:
            self.client.head_object(Bucket=self.target_bucket, Key=key)
            return False
        except ClientError as error:
            if error.response["Error"]["Code"] not in {"404", "NoSuchKey", "NotFound"}:
                raise

        buffer = io.BytesIO()
        pq.write_table(table, buffer, compression="snappy")
        self.client.put_object(Bucket=self.target_bucket, Key=key, Body=buffer.getvalue())
        return True

    def download_model(self, key: str) -> bytes:
        response = self.client.get_object(Bucket=self.target_bucket, Key=key)
        return response["Body"].read()
