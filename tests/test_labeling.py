"""Tests for pipewatch.labeling."""

from __future__ import annotations

import pytest

from pipewatch.labeling import LabelStore


@pytest.fixture
def store() -> LabelStore:
    return LabelStore()


def test_set_and_get_label(store: LabelStore) -> None:
    store.set("etl_daily", "team", "data-eng")
    assert store.get("etl_daily", "team") == "data-eng"


def test_get_missing_key_returns_none(store: LabelStore) -> None:
    assert store.get("etl_daily", "env") is None


def test_get_missing_pipeline_returns_none(store: LabelStore) -> None:
    assert store.get("nonexistent", "team") is None


def test_set_overwrites_existing_value(store: LabelStore) -> None:
    store.set("p1", "env", "staging")
    store.set("p1", "env", "production")
    assert store.get("p1", "env") == "production"


def test_remove_existing_label_returns_true(store: LabelStore) -> None:
    store.set("p1", "env", "prod")
    assert store.remove("p1", "env") is True
    assert store.get("p1", "env") is None


def test_remove_missing_label_returns_false(store: LabelStore) -> None:
    assert store.remove("p1", "env") is False


def test_get_all_returns_copy(store: LabelStore) -> None:
    store.set("p1", "team", "infra")
    store.set("p1", "env", "prod")
    labels = store.get_all("p1")
    assert labels == {"team": "infra", "env": "prod"}
    labels["extra"] = "x"
    assert store.get("p1", "extra") is None


def test_pipelines_with_label_key_only(store: LabelStore) -> None:
    store.set("p1", "env", "prod")
    store.set("p2", "env", "staging")
    store.set("p3", "team", "data")
    result = store.pipelines_with_label("env")
    assert result == ["p1", "p2"]


def test_pipelines_with_label_key_and_value(store: LabelStore) -> None:
    store.set("p1", "env", "prod")
    store.set("p2", "env", "staging")
    result = store.pipelines_with_label("env", "prod")
    assert result == ["p1"]


def test_all_pipelines_excludes_empty(store: LabelStore) -> None:
    store.set("p1", "env", "prod")
    store.set("p2", "team", "eng")
    store.clear_pipeline("p2")
    assert store.all_pipelines() == ["p1"]


def test_clear_pipeline_returns_count(store: LabelStore) -> None:
    store.set("p1", "env", "prod")
    store.set("p1", "team", "eng")
    assert store.clear_pipeline("p1") == 2
    assert store.get_all("p1") == {}


def test_iter_labels(store: LabelStore) -> None:
    store.set("p1", "env", "prod")
    store.set("p2", "team", "eng")
    entries = list(store.iter_labels())
    assert ("p1", "env", "prod") in entries
    assert ("p2", "team", "eng") in entries


def test_set_empty_pipeline_raises(store: LabelStore) -> None:
    with pytest.raises(ValueError, match="pipeline name"):
        store.set("", "key", "val")


def test_set_empty_key_raises(store: LabelStore) -> None:
    with pytest.raises(ValueError, match="label key"):
        store.set("p1", "", "val")
