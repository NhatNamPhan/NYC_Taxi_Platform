from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
import requests

from ingestion.download_data import download_atomic, main, validate_lookup
from pipeline.config import months


def response(chunks, length=None):
    result = MagicMock()
    result.__enter__.return_value = result
    result.headers = {} if length is None else {"Content-Length": str(length)}
    result.iter_content.return_value = chunks
    return result


def test_download_failure_propagates_and_removes_partial_file(tmp_path):
    def interrupted():
        yield b"partial"
        raise requests.ConnectionError("connection lost")
    target = tmp_path / "source.parquet"
    with patch("ingestion.download_data.requests.get", return_value=response(interrupted())):
        with pytest.raises(requests.ConnectionError):
            download_atomic("https://example.test/data", target, lambda _: None, attempts=1)
    assert not target.exists()
    assert not target.with_suffix(".parquet.part").exists()


def test_bad_http_status_never_publishes_file(tmp_path):
    result = response([])
    result.raise_for_status.side_effect = requests.HTTPError("404")
    with patch("ingestion.download_data.requests.get", return_value=result):
        with pytest.raises(requests.HTTPError):
            download_atomic("https://example.test/missing", tmp_path / "data", lambda _: None, attempts=1)
    assert not (tmp_path / "data").exists()


def test_length_mismatch_preserves_existing_file(tmp_path):
    target = tmp_path / "source"
    target.write_bytes(b"old")
    def reject_old(path):
        raise ValueError("bad source")
    with patch("ingestion.download_data.requests.get", return_value=response([b"new"], length=30)):
        with pytest.raises(ValueError, match="Incomplete"):
            download_atomic("https://example.test/data", target, reject_old, attempts=1)
    assert target.read_bytes() == b"old"


def test_validated_download_is_reused_without_network(tmp_path):
    target = tmp_path / "source"
    def validate(path):
        assert path.read_bytes() == b"complete"
    with patch("ingestion.download_data.requests.get", return_value=response([b"complete"], length=8)) as get:
        download_atomic("https://example.test/data", target, validate, attempts=1)
        download_atomic("https://example.test/data", target, validate, attempts=1)
    assert get.call_count == 1


def test_parallel_worker_error_fails_main():
    with patch("ingestion.download_data.download_atomic"), patch("ingestion.download_data.download_file", side_effect=RuntimeError("month missing")):
        with pytest.raises(RuntimeError, match="month missing"):
            main(["--start-month", "2025-01", "--end-month", "2025-02"])


@pytest.mark.parametrize("start,end", [("2025-13", "2025-14"), ("2025-1", "2025-01"), ("2025-02", "2025-01")])
def test_invalid_month_ranges(start, end):
    with pytest.raises(ValueError):
        list(months(start, end))


def test_month_range_crosses_year_boundary():
    assert list(months("2024-12", "2025-02")) == [(2024, 12), (2025, 1), (2025, 2)]


def test_versioned_lookup_is_complete():
    validate_lookup(Path(__file__).resolve().parents[1] / "dbt/seeds/taxi_zone_lookup.csv")
