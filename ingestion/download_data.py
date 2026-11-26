"""Download complete, validated source files independently of the working directory."""
import csv
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pyarrow.parquet as pq
import requests

from pipeline.config import DATA_DIR, PROJECT_ROOT, month_arguments, months

LOG = logging.getLogger(__name__)
BASE_URL = "https://d37ci6vzurychx.cloudfront.net"
LOOKUP_PATH = PROJECT_ROOT / "dbt" / "seeds" / "taxi_zone_lookup.csv"


def validate_parquet(path):
    parquet = pq.ParquetFile(path)
    if parquet.metadata.num_rows == 0:
        raise ValueError(f"Empty source: {path}")
    required = {"VendorID", "tpep_pickup_datetime", "tpep_dropoff_datetime", "PULocationID", "DOLocationID"}
    if not required.issubset(parquet.schema_arrow.names):
        raise ValueError(f"Unexpected taxi schema: {path}")


def validate_lookup(path):
    with open(path, encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not {"LocationID", "Borough", "Zone", "service_zone"}.issubset(reader.fieldnames or []):
            raise ValueError("Unexpected taxi zone lookup columns")
        ids = [int(row["LocationID"]) for row in reader]
    if set(ids) != set(range(1, 266)) or len(ids) != 265:
        raise ValueError("Lookup must contain each location 1..265 exactly once")


def download_atomic(url, destination, validator, attempts=3):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        try:
            validator(destination)
            LOG.info("Validated existing file: %s", destination.name)
            return destination
        except Exception:
            LOG.warning("Existing file is invalid; downloading a replacement: %s", destination.name)
    temporary = destination.with_suffix(destination.suffix + ".part")
    for attempt in range(attempts):
        try:
            with requests.get(url, stream=True, timeout=(15, 120), headers={"Accept-Encoding": "identity"}) as response:
                response.raise_for_status()
                size = 0
                with temporary.open("wb") as handle:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            size += handle.write(chunk)
                    handle.flush()
                    os.fsync(handle.fileno())
                expected = response.headers.get("Content-Length")
                if expected is not None and size != int(expected):
                    raise ValueError(f"Incomplete response: expected {expected} bytes, received {size}")
            validator(temporary)
            os.replace(temporary, destination)
            LOG.info("Downloaded and validated %s", destination.name)
            return destination
        except Exception:
            temporary.unlink(missing_ok=True)
            if attempt + 1 == attempts:
                raise
            LOG.warning("Download failed; retry %s/%s: %s", attempt + 2, attempts, destination.name)
            time.sleep(2 ** attempt)


def download_file(year_month):
    year, month = year_month
    filename = f"yellow_tripdata_{year}-{month:02d}.parquet"
    path = DATA_DIR / "bronze" / f"year={year}" / f"month={month:02d}" / filename
    return download_atomic(f"{BASE_URL}/trip-data/{filename}", path, validate_parquet)


def main(argv=None):
    args = month_arguments(__doc__, argv)
    download_atomic(f"{BASE_URL}/misc/taxi_zone_lookup.csv", LOOKUP_PATH, validate_lookup)
    with ThreadPoolExecutor(max_workers=4) as executor:
        # Consume results so any worker failure makes the command/Airflow task fail.
        list(executor.map(download_file, months(args.start_month, args.end_month)))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    main()
