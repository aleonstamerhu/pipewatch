"""Tests for pipewatch.labeling_cli."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

import pipewatch.labeling_cli as labeling_cli_module
from pipewatch.labeling import LabelStore
from pipewatch.labeling_cli import labeling


@pytest.fixture(autouse=True)
def fresh_store(monkeypatch: pytest.MonkeyPatch) -> LabelStore:
    store = LabelStore()
    monkeypatch.setattr(labeling_cli_module, "_get_store", lambda: store)
    return store


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_set_label(runner: CliRunner, fresh_store: LabelStore) -> None:
    result = runner.invoke(labeling, ["set", "etl_daily", "env", "prod"])
    assert result.exit_code == 0
    assert "env=prod" in result.output
    assert fresh_store.get("etl_daily", "env") == "prod"


def test_get_label_found(runner: CliRunner, fresh_store: LabelStore) -> None:
    fresh_store.set("etl_daily", "team", "data-eng")
    result = runner.invoke(labeling, ["get", "etl_daily", "team"])
    assert result.exit_code == 0
    assert "team=data-eng" in result.output


def test_get_label_missing(runner: CliRunner) -> None:
    result = runner.invoke(labeling, ["get", "etl_daily", "team"])
    assert result.exit_code == 0
    assert "not found" in result.output


def test_remove_label_exists(runner: CliRunner, fresh_store: LabelStore) -> None:
    fresh_store.set("p1", "env", "prod")
    result = runner.invoke(labeling, ["remove", "p1", "env"])
    assert result.exit_code == 0
    assert "Removed" in result.output
    assert fresh_store.get("p1", "env") is None


def test_remove_label_missing(runner: CliRunner) -> None:
    result = runner.invoke(labeling, ["remove", "p1", "env"])
    assert result.exit_code == 0
    assert "was not set" in result.output


def test_list_labels(runner: CliRunner, fresh_store: LabelStore) -> None:
    fresh_store.set("p1", "env", "prod")
    fresh_store.set("p1", "team", "eng")
    result = runner.invoke(labeling, ["list", "p1"])
    assert result.exit_code == 0
    assert "env=prod" in result.output
    assert "team=eng" in result.output


def test_list_labels_empty(runner: CliRunner) -> None:
    result = runner.invoke(labeling, ["list", "p1"])
    assert result.exit_code == 0
    assert "No labels" in result.output


def test_find_by_key(runner: CliRunner, fresh_store: LabelStore) -> None:
    fresh_store.set("p1", "env", "prod")
    fresh_store.set("p2", "env", "staging")
    result = runner.invoke(labeling, ["find", "env"])
    assert result.exit_code == 0
    assert "p1" in result.output
    assert "p2" in result.output


def test_find_by_key_and_value(runner: CliRunner, fresh_store: LabelStore) -> None:
    fresh_store.set("p1", "env", "prod")
    fresh_store.set("p2", "env", "staging")
    result = runner.invoke(labeling, ["find", "env", "--value", "prod"])
    assert result.exit_code == 0
    assert "p1" in result.output
    assert "p2" not in result.output


def test_find_no_results(runner: CliRunner) -> None:
    result = runner.invoke(labeling, ["find", "env"])
    assert result.exit_code == 0
    assert "No pipelines found" in result.output
