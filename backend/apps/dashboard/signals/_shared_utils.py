def get_email_context(action, instance, serializer_class):
    serializer = serializer_class(instance, context={'action': action})
    return serializer.data


def raise_error_for_direct_user_permission_assignment() -> None:
    """Raises an error describing that assigning a permission directly to user is prohibited.

    Raises:
        AssertionError: It's always raised, unconditionally.
    """
    raise AssertionError("Assigning permissions directly to users is prohibited. Instead, try assigning an appropriate group to the user.")
