from __future__ import annotations

import argparse
import json
from datetime import date

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

from .config import Settings
from .storage import S3ModelStore


def _read_model(store: S3ModelStore, prefix: str, ingested_on: date, model_name: str) -> pa.Table:
    key = store.model_key(prefix, ingested_on, model_name)
    return pq.read_table(pa.BufferReader(store.download_model(key)))


def summarize(settings: Settings, ingested_on: date) -> list[dict]:
    store = S3ModelStore(settings.source_bucket, settings.target_bucket, settings.region)
    connection = duckdb.connect()
    try:
        connection.register("fact_brewery_snapshot", _read_model(store, settings.mart_prefix, ingested_on, "fact_brewery_snapshot"))
        connection.register("dim_brewery_type", _read_model(store, settings.mart_prefix, ingested_on, "dim_brewery_type"))
        connection.register("dim_location", _read_model(store, settings.mart_prefix, ingested_on, "dim_location"))
        rows = connection.execute(
            """
            SELECT
              location.country,
              brewery_type.brewery_type,
              SUM(fact.brewery_count) AS breweries,
              SUM(CASE WHEN fact.is_closed THEN 1 ELSE 0 END) AS closed_breweries
            FROM fact_brewery_snapshot AS fact
            JOIN dim_brewery_type AS brewery_type USING (brewery_type_key)
            JOIN dim_location AS location USING (location_key)
            GROUP BY 1, 2
            ORDER BY breweries DESC, country, brewery_type
            """
        ).fetchall()
    finally:
        connection.close()
    return [
        {"country": country, "brewery_type": brewery_type, "breweries": breweries, "closed_breweries": closed}
        for country, brewery_type, breweries, closed in rows
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Query the brewery star schema with DuckDB")
    parser.add_argument("--ingested-date", required=True, type=date.fromisoformat)
    args = parser.parse_args()
    print(json.dumps(summarize(Settings.from_environment(), args.ingested_date), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
