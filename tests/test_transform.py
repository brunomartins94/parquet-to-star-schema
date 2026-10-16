from datetime import date

import pyarrow as pa

from star_schema.transform import build_model


def source_table() -> pa.Table:
    return pa.table(
        {
            "id": ["a", "b", "c"],
            "name": ["North", "South", "Closed"],
            "brewery_type": ["micro", "micro", "closed"],
            "city": ["Austin", "Austin", "Dallas"],
            "state_province": ["Texas", "Texas", "Texas"],
            "country": ["United States", "United States", "United States"],
        }
    )


def test_build_model_creates_dimensions_and_fact() -> None:
    model = build_model(source_table(), date(2026, 9, 26))

    assert model["dim_date"].to_pylist() == [{"date_key": 20260926, "calendar_date": "2026-09-26"}]
    assert model["dim_brewery"].num_rows == 3
    assert model["dim_brewery_type"].num_rows == 2
    assert model["dim_location"].num_rows == 2
    assert model["fact_brewery_snapshot"].num_rows == 3


def test_fact_marks_closed_breweries() -> None:
    model = build_model(source_table(), date(2026, 9, 26))
    facts = model["fact_brewery_snapshot"].to_pylist()

    assert sum(record["brewery_count"] for record in facts) == 3
    assert sum(record["is_closed"] for record in facts) == 1
