from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    source_bucket: str
    target_bucket: str
    region: str
    processed_prefix: str
    mart_prefix: str

    @classmethod
    def from_environment(cls) -> "Settings":
        load_dotenv()
        source_bucket = os.getenv("SOURCE_BUCKET", "").strip()
        target_bucket = os.getenv("TARGET_BUCKET", "").strip()
        if not source_bucket or not target_bucket:
            raise ValueError("SOURCE_BUCKET and TARGET_BUCKET must be configured")
        return cls(
            source_bucket=source_bucket,
            target_bucket=target_bucket,
            region=os.getenv("AWS_REGION", "us-east-2"),
            processed_prefix=os.getenv("PROCESSED_PREFIX", "processed/open_brewery_db"),
            mart_prefix=os.getenv("MART_PREFIX", "marts/brewery_directory"),
        )
