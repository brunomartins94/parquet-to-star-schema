from __future__ import annotations

import argparse
import json
import logging
from datetime import date

from .config import Settings
from .storage import S3ModelStore
from .transform import build_model

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def run(settings: Settings, ingested_on: date) -> dict[str, int]:
    store = S3ModelStore(settings.source_bucket, settings.target_bucket, settings.region)
    source = store.read_source(store.source_key(settings.processed_prefix, ingested_on))
    model = build_model(source, ingested_on)
    written = 0
    for model_name, table in model.items():
        key = store.model_key(settings.mart_prefix, ingested_on, model_name)
        written += int(store.write_if_missing(key, table))
    return {"source_records": source.num_rows, "models": len(model), "written_models": written}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a brewery analytics star schema from S3 Parquet")
    parser.add_argument("--ingested-date", required=True, type=date.fromisoformat)
    args = parser.parse_args()
    result = run(Settings.from_environment(), args.ingested_date)
    logging.info("model_finished %s", json.dumps(result))


if __name__ == "__main__":
    main()
