from __future__ import unicode_literals

import copy
import re


KEY_ARRAY_RE = re.compile('(?P<key>[A-Za-z]+)(\[(?P<index>[0-9])*\])?')


def is_key_array(key):
    return re.match(KEY_ARRAY_RE, key)


class ActionError(Exception):
    pass


class TokenError(Exception):
    pass


class Action(object):

    ADD = 'add'
    APPEND = 'append'
    ADD_OR_REPLACE = 'add_or_replace'
    REPLACE = 'replace'
    DELETE = 'delete'

    __slots__ = ['type', 'path', 'value']

    def __init__(self, type_, path, value=None):
        self.type = type_
        self.path = path.split('.')
        self.value = value

    def __eq__(self, other):
        return isinstance(other, Action) \
            and self.type == other.type \
            and self.path == other.path \
            and self.value == other.value


class IncrementalObject(object):

    def __init__(self, initial_object=None):
        self._initial_object = None

        self.actions = []

        self.set(initial_object)

    def _format_partial_path(self, path, index):
        return '.'.join(path[:index + 1])

    def _get_node_info_from_token(self, token):
        match = KEY_ARRAY_RE.match(token)

        if not match:
            raise TokenError("Token {} is not valid".format(token))

        info = match.groupdict()
        key = info['key']
        index = info.get('index')

        if index is not None:
            index = int(index)

        return key, index

    def _get_node_from_path(self, node, path, fail_on_missing=False):
        # Follow path
        for path_index, token in enumerate(path):
            key, index = self._get_node_info_from_token(token)

            # Check key in node
            if key not in node and fail_on_missing:
                raise KeyError(self._format_partial_path(path, path_index))

            node = node[key]

            # Node is an array
            if index is not None:
                if not isinstance(node, list):
                    raise ValueError(
                        'Node {} is not an array'
                        .format(self._format_partial_path(path, path_index))
                    )

                node = node[index]

        # Return node
        return node

    def _apply_actions(self):
        obj = copy.deepcopy(self._initial_object)

        for action in self.actions:
            if action.type == Action.ADD:
                obj = self._apply_action_add(obj, action)
            elif action.type == Action.APPEND:
                obj = self._apply_action_append(obj, action)
            elif action.type == Action.DELETE:
                obj = self._apply_action_delete(obj, action)
            elif action.type == Action.REPLACE:
                obj = self._apply_action_replace(obj, action)
            elif action.type == Action.ADD_OR_REPLACE:
                obj = self._apply_action_add_or_replace(obj, action)

        return obj

    def _apply_action_replace(self, obj, action):
        # Get node
        node = self._get_node_from_path(obj, action.path[:-1], fail_on_missing=True)

        # Replace value
        key = action.path[-1]

        if key not in node:
            raise ActionError(
                "Cannot replace path {} because doesn't exist".format('.'.join(action.path))
            )

        node[key] = action.value

        return obj

    def _apply_action_add_or_replace(self, obj, action):
        # Get node
        node = self._get_node_from_path(obj, action.path[:-1], fail_on_missing=True)

        # Add or replace value
        key = action.path[-1]
        node[key] = action.value

        return obj

    def _apply_action_add(self, obj, action):
        # Get parent node
        node = self._get_node_from_path(obj, action.path[:-1], fail_on_missing=True)

        # Add value
        value = action.value
        key = action.path[-1]

        if key in node:
            raise ActionError('Cannot add {} because already present'.format(action.path))

        node[key] = value

        return obj

    def _apply_action_append(self, obj, action):
        # Get parent node
        node = self._get_node_from_path(obj, action.path[:-1], fail_on_missing=True)

        # Append value
        value = action.value
        key = action.path[-1]

        node[key].append(value)

        return obj

    def _apply_action_delete(self, obj, action):
        # Get node
        node = self._get_node_from_path(obj, action.path[:-1], fail_on_missing=True)

        # Remove key
        token = action.path[-1]
        key, index = self._get_node_info_from_token(token)

        if index is not None:
            # Item is an array
            node[key].pop(index)
        elif key in node:
            # Item is an object and key does exists
            del node[key]

        return obj

    @property
    def current_object(self):
        return self._apply_actions()

    @property
    def initial_object(self):
        return copy.deepcopy(self._initial_object)

    def squash(self):
        self.set(self.current_object)
        self.actions = []

    def set(self, initial_object, rebase=False):
        self._initial_object = initial_object or {}

    def add(self, path, value):
        self.actions.append(Action(Action.ADD, path, value))

    def append(self, path, value):
        self.actions.append(Action(Action.APPEND, path, value))

    def delete(self, path):
        self.actions.append(Action(Action.DELETE, path))

    def replace(self, path, value):
        self.actions.append(Action(Action.REPLACE, path, value))

    def add_or_replace(self, path, value):
        self.actions.append(Action(Action.ADD_OR_REPLACE, path, value))
