"""Tests for pipewatch.tagging."""

import pytest

from pipewatch.tagging import TagStore


@pytest.fixture
def store() -> TagStore:
    return TagStore()


def test_add_single_tag(store: TagStore) -> None:
    store.add("etl_sales", "production")
    assert store.get("etl_sales") == ["production"]


def test_add_multiple_tags(store: TagStore) -> None:
    store.add("etl_sales", "production", "critical", "nightly")
    assert store.get("etl_sales") == ["critical", "nightly", "production"]


def test_tags_are_lowercased(store: TagStore) -> None:
    store.add("pipe", "PRODUCTION", "Nightly")
    assert store.get("pipe") == ["nightly", "production"]


def test_add_duplicate_tag_is_idempotent(store: TagStore) -> None:
    store.add("pipe", "critical")
    store.add("pipe", "critical")
    assert store.get("pipe") == ["critical"]


def test_get_unknown_pipeline_returns_empty(store: TagStore) -> None:
    assert store.get("nonexistent") == []


def test_remove_existing_tag_returns_true(store: TagStore) -> None:
    store.add("pipe", "staging")
    result = store.remove("pipe", "staging")
    assert result is True
    assert store.get("pipe") == []


def test_remove_nonexistent_tag_returns_false(store: TagStore) -> None:
    result = store.remove("pipe", "ghost")
    assert result is False


def test_pipelines_with_tag(store: TagStore) -> None:
    store.add("pipe_a", "production")
    store.add("pipe_b", "staging")
    store.add("pipe_c", "production")
    assert store.pipelines_with_tag("production") == ["pipe_a", "pipe_c"]


def test_pipelines_with_tag_case_insensitive(store: TagStore) -> None:
    store.add("pipe", "production")
    assert store.pipelines_with_tag("PRODUCTION") == ["pipe"]


def test_all_tags_returns_unique_sorted(store: TagStore) -> None:
    store.add("pipe_a", "critical", "nightly")
    store.add("pipe_b", "nightly", "staging")
    assert store.all_tags() == ["critical", "nightly", "staging"]


def test_clear_specific_pipeline(store: TagStore) -> None:
    store.add("pipe_a", "critical")
    store.add("pipe_b", "staging")
    store.clear("pipe_a")
    assert store.get("pipe_a") == []
    assert store.get("pipe_b") == ["staging"]


def test_clear_all(store: TagStore) -> None:
    store.add("pipe_a", "critical")
    store.add("pipe_b", "staging")
    store.clear()
    assert store.all_tags() == []


def test_empty_pipeline_name_raises(store: TagStore) -> None:
    with pytest.raises(ValueError, match="pipeline name"):
        store.add("", "critical")


def test_empty_tag_raises(store: TagStore) -> None:
    with pytest.raises(ValueError, match="tag"):
        store.add("pipe", "  ")
