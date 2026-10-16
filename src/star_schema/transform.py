from __future__ import annotations

import hashlib
from datetime import date

import pyarrow as pa


def _key(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _text(value: object) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def build_model(source: pa.Table, ingested_on: date) -> dict[str, pa.Table]:
    required = {"id", "name", "brewery_type", "city", "state_province", "country"}
    missing = required - set(source.column_names)
    if missing:
        raise ValueError(f"Source Parquet is missing columns: {', '.join(sorted(missing))}")

    brewery_types: dict[str, dict] = {}
    locations: dict[str, dict] = {}
    breweries: dict[str, dict] = {}
    facts: list[dict] = []

    for record in source.to_pylist():
        brewery_id = _text(record["id"])
        if brewery_id is None:
            raise ValueError("Source record is missing brewery id")

        type_name = _text(record["brewery_type"]) or "unknown"
        type_key = _key(f"type|{type_name.lower()}")
        brewery_types.setdefault(type_key, {"brewery_type_key": type_key, "brewery_type": type_name})

        city = _text(record["city"])
        state_province = _text(record["state_province"])
        country = _text(record["country"]) or "unknown"
        location_key = _key(f"location|{country.lower()}|{state_province or ''}|{city or ''}")
        locations.setdefault(
            location_key,
            {
                "location_key": location_key,
                "city": city,
                "state_province": state_province,
                "country": country,
            },
        )

        brewery_key = _key(f"brewery|{brewery_id}")
        breweries[brewery_key] = {
            "brewery_key": brewery_key,
            "brewery_id": brewery_id,
            "brewery_name": _text(record["name"]) or "unknown",
            "brewery_type_key": type_key,
            "location_key": location_key,
        }
        facts.append(
            {
                "snapshot_date_key": int(ingested_on.strftime("%Y%m%d")),
                "brewery_key": brewery_key,
                "brewery_type_key": type_key,
                "location_key": location_key,
                "brewery_count": 1,
                "is_closed": type_name.lower() == "closed",
            }
        )

    return {
        "dim_date": pa.Table.from_pylist(
            [{"date_key": int(ingested_on.strftime("%Y%m%d")), "calendar_date": ingested_on.isoformat()}]
        ),
        "dim_brewery_type": pa.Table.from_pylist(list(brewery_types.values())),
        "dim_location": pa.Table.from_pylist(list(locations.values())),
        "dim_brewery": pa.Table.from_pylist(list(breweries.values())),
        "fact_brewery_snapshot": pa.Table.from_pylist(facts),
    }
