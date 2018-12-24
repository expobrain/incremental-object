import copy


class ActionError(Exception):
    pass


class TokenError(Exception):
    pass


ADD = "add"
REPLACE = "replace"
DELETE = "delete"
ADD_OR_REPLACE = "add_or_replace"


def _normalise_path_token(node, token):
    if isinstance(node, list):
        try:
            return int(token)
        except ValueError:
            raise IndexError(
                "Node {} is an array but token {} is not a valid index".format(node, token)
            )

    return token


def _get_node_from_path(node, path, fail_on_missing=False):
    # Follow path
    for token in path:
        # Normalise token for arrays
        token = _normalise_path_token(node, token)

        # Extract node
        try:
            node = node[token]
        except (IndexError, KeyError):
            if not fail_on_missing:
                return None
            else:
                raise

    # Return node
    return node


def _apply_action_replace(obj, path, value):
    # Get node and token
    node = _get_node_from_path(obj, path[:-1], fail_on_missing=True)
    token = _normalise_path_token(node, path[-1])

    # Check value exists
    if isinstance(node, list):
        node_len = len(node)
        index = (node_len - token) if token < 0 else token

        if index >= node_len or index < 0:
            raise ActionError(
                "Cannot replace item {} in path {} because out of index".format(index, path)
            )
    elif token not in node:
        raise ActionError("Cannot replace path {} because doesn't exist".format(path))

    # Replace value
    node[token] = value

    return obj


def _apply_action_add(obj, path, value):
    # Get parent node
    key = path[-1]

    parent_node = _get_node_from_path(obj, path[:-1], fail_on_missing=True)
    child_node = _get_node_from_path(parent_node, path[-1:])

    if isinstance(child_node, list):
        # Add value to array
        child_node.append(value)

    elif child_node is not None:
        # Child node is missing
        raise ActionError("Cannot add {} because already present".format(path))

    else:
        # Add object key
        parent_node[key] = value

    return obj


def _apply_action_add_or_replace(obj, path, value):
    # Get parent node
    parent_node = _get_node_from_path(obj, path[:-1], fail_on_missing=True)
    child_node = _get_node_from_path(parent_node, path[-1:])

    # If parent node is a list means that the parent node is the list
    # we need to modify
    if isinstance(parent_node, list):
        node = parent_node
    else:
        node = child_node

    # Compute key
    key = _normalise_path_token(node, path[-1])

    # Update path with value
    if isinstance(node, list):
        if key < len(parent_node):
            parent_node[key] = value
        else:
            parent_node.append(value)
    else:
        # Update object key
        parent_node[key] = value

    return obj


def _apply_action_delete(obj, path, value=None):
    # Get node
    node = _get_node_from_path(obj, path[:-1], fail_on_missing=True)

    # Remove key
    key = _normalise_path_token(node, path[-1])

    if isinstance(node, list) and key < len(node):
        node.pop(key)
    elif key in node:
        del node[key]

    return obj


def incremental_change(obj, op, path, value=None):
    if op == ADD:
        fn = _apply_action_add
    elif op == DELETE:
        fn = _apply_action_delete
    elif op == REPLACE:
        fn = _apply_action_replace
    elif op == ADD_OR_REPLACE:
        fn = _apply_action_add_or_replace
    else:
        raise ValueError(op)

    obj = copy.deepcopy(obj)
    obj = fn(obj, path, value)

    return obj
