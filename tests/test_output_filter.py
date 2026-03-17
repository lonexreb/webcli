"""Tests for output filtering."""

from __future__ import annotations

from site2cli.output_filter import filter_result


def test_grep_filters_keys():
    data = {"user_name": "alice", "user_email": "a@b.com", "id": 1}
    result = filter_result(data, grep="user")
    assert "user_name" in result
    assert "user_email" in result
    assert "id" not in result


def test_grep_regex():
    data = {"get_users": [], "post_users": [], "get_items": []}
    result = filter_result(data, grep="^get")
    assert "get_users" in result
    assert "get_items" in result
    assert "post_users" not in result


def test_limit_truncates_list():
    data = [1, 2, 3, 4, 5]
    result = filter_result(data, limit=3)
    assert result == [1, 2, 3]


def test_limit_on_dict_list_values():
    data = {"items": [1, 2, 3, 4, 5], "name": "test"}
    result = filter_result(data, limit=2)
    assert result["items"] == [1, 2]
    assert result["name"] == "test"


def test_keys_only():
    data = {"name": "alice", "email": "a@b.com", "age": 30}
    result = filter_result(data, keys_only=True)
    assert sorted(result) == ["age", "email", "name"]


def test_no_filters_passthrough():
    data = {"key": "value"}
    result = filter_result(data)
    assert result == {"key": "value"}


def test_combined_grep_and_limit():
    data = {"items": [1, 2, 3], "other": [4, 5, 6]}
    result = filter_result(data, grep="items", limit=2)
    assert "items" in result
    assert "other" not in result
    assert result["items"] == [1, 2]


def test_list_passthrough_with_no_limit():
    data = [1, 2, 3]
    result = filter_result(data)
    assert result == [1, 2, 3]
