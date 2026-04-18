"""Tests for PipelineMetric data structure and status computation."""

from datetime import datetime

import pytest

from pipewatch.metrics import PipelineMetric, MetricStatus


def make_metric(**kwargs) -> PipelineMetric:
    defaults = dict(
        pipeline_name="test_pipe",
        rows_processed=1000,
        error_count=0,
        duration_seconds=60.0,
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
    )
    defaults.update(kwargs)
    return PipelineMetric(**defaults)


def test_default_status_is_unknown():
    m = make_metric()
    assert m.status == MetricStatus.UNKNOWN


def test_ok_status():
    m = make_metric(error_count=0, duration_seconds=100.0)
    status = m.compute_status(max_errors=0, max_duration_seconds=300.0)
    assert status == MetricStatus.OK


def test_critical_on_errors():
    m = make_metric(error_count=5)
    status = m.compute_status(max_errors=0)
    assert status == MetricStatus.CRITICAL


def test_critical_on_duration():
    m = make_metric(duration_seconds=400.0)
    status = m.compute_status(max_duration_seconds=300.0)
    assert status == MetricStatus.CRITICAL


def test_warning_on_borderline_duration():
    m = make_metric(error_count=0, duration_seconds=250.0)
    status = m.compute_status(max_errors=0, max_duration_seconds=300.0)
    assert status == MetricStatus.WARNING


def test_to_dict_contains_expected_keys():
    m = make_metric()
    m.compute_status()
    d = m.to_dict()
    assert set(d.keys()) == {
        "pipeline_name", "rows_processed", "error_count",
        "duration_seconds", "timestamp", "status",
    }
    assert d["pipeline_name"] == "test_pipe"
