from datetime import date

import io

import pyarrow as pa
import pyarrow.parquet as pq

from star_schema import analysis
from star_schema.config import Settings
from star_schema.transform import build_model


def parquet_bytes(table: pa.Table) -> bytes:
    buffer = io.BytesIO()
    pq.write_table(table, buffer)
    return buffer.getvalue()


def test_summarize_joins_fact_and_dimensions(monkeypatch) -> None:
    source = pa.table(
        {
            "id": ["a", "b"],
            "name": ["One", "Two"],
            "brewery_type": ["micro", "closed"],
            "city": ["Austin", "Dallas"],
            "state_province": ["Texas", "Texas"],
            "country": ["United States", "United States"],
        }
    )
    model = build_model(source, date(2026, 9, 26))

    class FakeStore:
        def __init__(self, *_args):
            pass

        @staticmethod
        def model_key(_prefix, _date, model_name):
            return model_name

        @staticmethod
        def download_model(model_name):
            return parquet_bytes(model[model_name])

    monkeypatch.setattr(analysis, "S3ModelStore", FakeStore)
    settings = Settings("source", "target", "us-east-2", "processed", "marts")

    assert analysis.summarize(settings, date(2026, 9, 26)) == [
        {"country": "United States", "brewery_type": "closed", "breweries": 1, "closed_breweries": 1},
        {"country": "United States", "brewery_type": "micro", "breweries": 1, "closed_breweries": 0},
    ]
