"""Month selection shared by ingestion, Spark, dbt and Airflow."""
import argparse
from datetime import date
import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")
DATA_DIR = Path(os.getenv("TAXI_DATA_DIR", str(PROJECT_ROOT / "data"))).resolve()


def parse_month(value):
    try:
        result = date.fromisoformat(f"{value}-01")
        if result.strftime("%Y-%m") != value:
            raise ValueError
        return result
    except (ValueError, TypeError) as error:
        raise ValueError(f"Expected YYYY-MM, received {value!r}") from error


def next_month(value):
    return date(value.year + (value.month == 12), value.month % 12 + 1, 1)


def months(start, end):
    current, last = parse_month(start), parse_month(end)
    if current > last:
        raise ValueError("start-month must not be after end-month")
    while current <= last:
        yield current.year, current.month
        current = next_month(current)


def month_arguments(description, argv=None):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--start-month", default=os.getenv("PIPELINE_START_MONTH", "2025-01"))
    parser.add_argument("--end-month", default=os.getenv("PIPELINE_END_MONTH", "2025-01"))
    args = parser.parse_args(argv)
    try:
        list(months(args.start_month, args.end_month))
    except ValueError as error:
        parser.error(str(error))
    return args


def partition_path(layer, year, month):
    return DATA_DIR / layer / f"year={year}" / f"month={month:02d}"
