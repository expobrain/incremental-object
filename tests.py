from __future__ import unicode_literals

import unittest

import pytest

from incremental_object import IncrementalObject, ActionError, Action


class ActionTests(unittest.TestCase):

    def test_equality(self):
        action1 = Action(Action.ADD, 'value', 42)
        action2 = Action(Action.ADD, 'value', 42)

        assert action1 == action2

    def test_inequality(self):
        action1 = Action(Action.ADD, 'value', 42)
        action2 = Action(Action.ADD, 'value', 43)

        assert action1 != action2


class IncrementalObjectTests(unittest.TestCase):

    def setUp(self):
        self.object = IncrementalObject()

    def test_set(self):
        value = {'value': 42}

        self.object.set(value)

        assert self.object.current_object == value

    def test_squash(self):
        self.object.add('value', 42)

        assert self.object.initial_object == {}
        assert self.object.actions == [Action(Action.ADD, 'value', 42)]

        self.object.squash()

        assert self.object._initial_object == {'value': 42}
        assert self.object.actions == []

    # ------------------------------------------------------------
    # Append
    # ------------------------------------------------------------

    def test_append(self):
        self.object.set({'array': []})
        self.object.append('array', 42)

        assert self.object.current_object == {'array': [42]}

    def test_append_with_set(self):
        self.object.set({'array': []})
        self.object.append('array', 42)
        self.object.set({'array': [43]})

        assert self.object.current_object == {'array': [43, 42]}

    def test_append_deeper_path(self):
        self.object.set({
            'first': {
                'second': []
            }
        })
        self.object.append('first.second', 42)

        assert self.object.current_object == {
            'first': {
                'second': [42]
            }
        }

    # ------------------------------------------------------------
    # Add
    # ------------------------------------------------------------

    def test_add(self):
        self.object.add('value', 42)

        assert self.object.current_object == {'value': 42}

    def test_add_deeper_path(self):
        self.object.set({'first': {}})
        self.object.add('first.second', 42)

        assert self.object.current_object == {
            'first': {
                'second': 42
            }
        }

    def test_add_fail_because_existent(self):
        self.object.set({'value': 42})
        self.object.add('value', 42)

        with pytest.raises(ActionError):
            self.object.current_object

    def test_add_deeper_path_traversing_array(self):
        self.object.set({
            'first': [{}]
        })
        self.object.add('first[0].second', 42)

        assert self.object.current_object == {
            'first': [{
                'second': 42
            }]
        }

    # ------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------

    def test_delete(self):
        self.object.set({'value': 42})
        self.object.delete('value')

        assert self.object.current_object == {}

    def test_delete_deeper_path(self):
        self.object.set({
            'first': {
                'second': 42
            }
        })
        self.object.delete('first.second')

        assert self.object.current_object == {
            'first': {}
        }

    def test_delete_non_existent(self):
        self.object.delete('value')

        assert self.object.current_object == {}

    def test_delete_item_in_array(self):
        self.object.set({'array': [42]})
        self.object.delete('array[0]')

        assert self.object.current_object == {'array': []}

    # ------------------------------------------------------------
    # Replace
    # ------------------------------------------------------------

    def test_replace(self):
        self.object.set({'value': 42})
        self.object.replace('value', 43)

        assert self.object.current_object == {'value': 43}

    def test_replace_deeper_path(self):
        self.object.set({
            'first': {
                'second': 42
            }
        })
        self.object.replace('first.second', 43)

        assert self.object.current_object == {
            'first': {
                'second': 43
            }
        }

    def test_replace_fail_because_not_existent(self):
        self.object.replace('value', 42)

        with pytest.raises(ActionError):
            self.object.current_object

    # ------------------------------------------------------------
    # Add or replace
    # ------------------------------------------------------------

    def test_add_or_replace_non_existent_value(self):
        self.object.add_or_replace('value', 42)

        assert self.object.current_object == {'value': 42}

    def test_add_or_replace_deeper_path_non_existent_value(self):
        self.object.set({
            'first': {}
        })
        self.object.add_or_replace('first.second', 42)

        assert self.object.current_object == {
            'first': {
                'second': 42
            }
        }

    def test_add_or_replace_existing_value(self):
        self.object.set({'value': 42})
        self.object.add_or_replace('value', 43)

        assert self.object.current_object == {'value': 43}

    def test_add_or_replace_deeper_path_existent_value(self):
        self.object.set({
            'first': {
                'second': 42
            }
        })
        self.object.add_or_replace('first.second', 43)

        assert self.object.current_object == {
            'first': {
                'second': 43
            }
        }
