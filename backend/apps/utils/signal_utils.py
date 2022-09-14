from functools import wraps

ACTION_UPDATED = "Updated"
ACTION_CREATED = "Created"
ACTION_DELETED = "Deleted"


def with_action(func):
    """
    Embed action argument with value Deleted/Created/Updated
    based on model signals post_save, post_delete in decorated function.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if kwargs.get('created') is None:
            action = ACTION_DELETED
        elif kwargs.get('created'):
            action = ACTION_CREATED
        else:
            action = ACTION_UPDATED

        return func(action, *args, **kwargs)
    return wrapper
