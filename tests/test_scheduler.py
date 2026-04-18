"""Tests for pipewatch.scheduler."""

import time
import pytest
from unittest.mock import MagicMock
from pipewatch.scheduler import Scheduler, ScheduledJob


@pytest.fixture
def scheduler():
    s = Scheduler()
    yield s
    s.stop()


def test_add_and_list_jobs(scheduler):
    scheduler.add_job("pipe_a", 60, lambda n: None)
    scheduler.add_job("pipe_b", 30, lambda n: None)
    assert set(scheduler.list_jobs()) == {"pipe_a", "pipe_b"}


def test_remove_job(scheduler):
    scheduler.add_job("pipe_a", 60, lambda n: None)
    result = scheduler.remove_job("pipe_a")
    assert result is True
    assert "pipe_a" not in scheduler.list_jobs()


def test_remove_nonexistent_job(scheduler):
    result = scheduler.remove_job("ghost")
    assert result is False


def test_job_is_due_when_interval_elapsed():
    job = ScheduledJob("p", interval_seconds=5, callback=lambda n: None, last_run=0.0)
    assert job.is_due(time.time()) is True


def test_job_not_due_when_recent():
    job = ScheduledJob("p", interval_seconds=60, callback=lambda n: None, last_run=time.time())
    assert job.is_due(time.time()) is False


def test_job_not_due_when_disabled():
    job = ScheduledJob("p", interval_seconds=0, callback=lambda n: None, last_run=0.0, enabled=False)
    assert job.is_due(time.time()) is False


def test_callback_invoked_on_tick(scheduler):
    called_with = []
    scheduler.add_job("pipe_x", 1, lambda name: called_with.append(name))
    scheduler.start()
    time.sleep(2.5)
    scheduler.stop()
    assert called_with.count("pipe_x") >= 1


def test_start_stop_idempotent(scheduler):
    scheduler.start()
    scheduler.start()  # second call should be no-op
    scheduler.stop()
    scheduler.stop()  # should not raise
