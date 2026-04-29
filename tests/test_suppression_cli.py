"""Tests for pipewatch.suppression_cli."""
from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from pipewatch.suppression import SuppressionRule, SuppressionStore
from pipewatch.suppression_cli import suppression


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def fresh_store():
    store = SuppressionStore()
    with patch("pipewatch.suppression_cli._get_store", return_value=store):
        yield store


def test_add_rule_permanent(runner, fresh_store):
    result = runner.invoke(suppression, ["add", "etl"])
    assert result.exit_code == 0
    assert "permanent" in result.output
    assert len(fresh_store.active_rules()) == 1


def test_add_rule_with_duration_and_severity(runner, fresh_store):
    result = runner.invoke(suppression, ["add", "etl", "--severity", "critical", "--minutes", "60"])
    assert result.exit_code == 0
    assert "60m" in result.output
    assert "critical" in result.output


def test_add_rule_with_reason(runner, fresh_store):
    result = runner.invoke(suppression, ["add", "etl", "--reason", "planned maintenance"])
    assert result.exit_code == 0
    assert "planned maintenance" in result.output


def test_list_no_rules(runner, fresh_store):
    result = runner.invoke(suppression, ["list"])
    assert result.exit_code == 0
    assert "No active" in result.output


def test_list_shows_active_rules(runner, fresh_store):
    fresh_store.add(SuppressionRule(pipeline="etl", severity="warning", expires_at=None, reason="test"))
    result = runner.invoke(suppression, ["list"])
    assert result.exit_code == 0
    assert "etl" in result.output
    assert "warning" in result.output


def test_remove_existing_rule(runner, fresh_store):
    from pipewatch.suppression import make_suppression_rule
    fresh_store.add(make_suppression_rule("etl", severity="critical"))
    result = runner.invoke(suppression, ["remove", "etl", "--severity", "critical"])
    assert result.exit_code == 0
    assert "Removed 1" in result.output


def test_remove_nonexistent_rule(runner, fresh_store):
    result = runner.invoke(suppression, ["remove", "ghost"])
    assert result.exit_code == 0
    assert "No matching" in result.output


def test_purge_expired(runner, fresh_store):
    past = datetime.utcnow() - timedelta(seconds=10)
    fresh_store.add(SuppressionRule(pipeline="etl", severity=None, expires_at=past))
    result = runner.invoke(suppression, ["purge"])
    assert result.exit_code == 0
    assert "Purged 1" in result.output
    assert len(fresh_store.active_rules()) == 0
