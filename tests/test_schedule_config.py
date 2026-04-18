"""Tests for pipewatch.schedule_config."""

import pytest
from pipewatch.schedule_config import JobConfig, parse_job_configs


def test_parse_valid_configs():
    raw = [
        {"pipeline_name": "etl_daily", "interval_seconds": 3600},
        {"pipeline_name": "etl_hourly", "interval_seconds": 60},
    ]
    configs = parse_job_configs(raw)
    assert len(configs) == 2
    assert configs[0].pipeline_name == "etl_daily"
    assert configs[1].interval_seconds == 60


def test_empty_list():
    assert parse_job_configs([]) == []


def test_invalid_pipeline_name_raises():
    raw = [{"pipeline_name": "", "interval_seconds": 60}]
    with pytest.raises(ValueError, match="pipeline_name"):
        parse_job_configs(raw)


def test_invalid_interval_raises():
    raw = [{"pipeline_name": "pipe", "interval_seconds": 0}]
    with pytest.raises(ValueError, match="interval_seconds"):
        parse_job_configs(raw)


def test_negative_interval_raises():
    raw = [{"pipeline_name": "pipe", "interval_seconds": -10}]
    with pytest.raises(ValueError):
        parse_job_configs(raw)


def test_job_config_validate_ok():
    cfg = JobConfig(pipeline_name="ok_pipe", interval_seconds=30)
    cfg.validate()  # should not raise
