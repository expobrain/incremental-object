import unittest

import pytest

from incremental_object import (
    incremental_change,
    ActionError,
    ADD,
    ADD_OR_REPLACE,
    REPLACE,
    DELETE,
)


# ------------------------------------------------------------
# Add
# ------------------------------------------------------------


def test_add():
    obj = {}

    result = incremental_change(obj, ADD, ["value"], 42)

    assert result == {"value": 42}


def test_add_array():
    obj = {"array": []}

    result = incremental_change(obj, ADD, ["array"], 42)

    assert result == {"array": [42]}


def test_add_deeper_path():
    obj = {"first": {}}

    result = incremental_change(obj, ADD, ["first", "second"], 42)

    assert result == {"first": {"second": 42}}


def test_add_fail_because_existent():
    obj = {"value": 42}

    with pytest.raises(ActionError):
        incremental_change(obj, ADD, ["value"], 42)


def test_add_deeper_path_traversing_array():
    obj = {"first": [{}]}

    result = incremental_change(obj, ADD, ["first", 0, "second"], 42)

    assert result == {"first": [{"second": 42}]}


# ------------------------------------------------------------
# Replace
# ------------------------------------------------------------


def test_replace():
    obj = {"value": 42}

    result = incremental_change(obj, REPLACE, ["value"], 43)

    assert result == {"value": 43}


def test_replace_deeper_path():
    obj = {"first": {"second": 42}}

    result = incremental_change(obj, REPLACE, ["first", "second"], 43)

    assert result == {"first": {"second": 43}}


def test_replace_array():
    obj = {"array": [42]}

    result = incremental_change(obj, REPLACE, ["array", 0], 43)

    assert result == {"array": [43]}


def test_replace_nested_array():
    obj = {"object": {"array": [42]}}

    result = incremental_change(obj, REPLACE, ["object", "array", "0"], 43)

    assert result == {"object": {"array": [43]}}


def test_replace_fail_because_not_existent():
    obj = {}

    with pytest.raises(ActionError):
        incremental_change(obj, REPLACE, ["value"], 42)


def test_replace_fail_because_out_of_bound():
    obj = {"values": []}

    with pytest.raises(ActionError):
        incremental_change(obj, REPLACE, ["values", 0], 42)


# ------------------------------------------------------------
# Add or replace
# ------------------------------------------------------------


def test_add_or_replace_non_existent_value():
    obj = {}

    result = incremental_change(obj, ADD_OR_REPLACE, ["value"], 42)

    assert result == {"value": 42}


def test_add_or_replace_deeper_path_non_existent_value():
    obj = {"first": {}}

    result = incremental_change(obj, ADD_OR_REPLACE, ["first", "second"], 42)

    assert result == {"first": {"second": 42}}


def test_add_or_replace_existing_value():
    obj = {"value": 42}

    result = incremental_change(obj, ADD_OR_REPLACE, ["value"], 43)

    assert result == {"value": 43}


def test_add_or_replace_deeper_path_existent_value():
    obj = {"first": {"second": 42}}

    result = incremental_change(obj, ADD_OR_REPLACE, ["first", "second"], 43)

    assert result == {"first": {"second": 43}}


def test_add_or_replace_existing_list_value():
    obj = {"first": {"second": ["old_value"]}}

    result = incremental_change(obj, ADD_OR_REPLACE, ["first", "second", "0"], "new_value")

    assert result == {"first": {"second": ["new_value"]}}


def test_add_or_replace_nested_array():
    obj = {"object": {"array": []}}

    result = incremental_change(obj, ADD_OR_REPLACE, ["object", "array", "1"], 42)

    assert result == {"object": {"array": [42]}}


# ------------------------------------------------------------
# Delete
# ------------------------------------------------------------


def test_delete():
    obj = {"value": 42}

    result = incremental_change(obj, DELETE, ["value"])

    assert result == {}


def test_delete_deeper_path():
    obj = {"first": {"second": 42}}

    result = incremental_change(obj, DELETE, ["first", "second"])

    assert result == {"first": {}}


def test_delete_non_existent():
    obj = {}

    result = incremental_change(obj, DELETE, ["value"])

    assert result == {}


def test_delete_item_in_array():
    obj = {"array": [42]}

    result = incremental_change(obj, DELETE, ["array", 0])

    assert result == {"array": []}


def test_delete_item_in_nested_array():
    obj = {"object": {"array": [42]}}

    result = incremental_change(obj, DELETE, ["object", "array", "0"])

    assert result == {"object": {"array": []}}
