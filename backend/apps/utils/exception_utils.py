from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.status import is_server_error
from sentry_sdk import capture_exception
from django.db import IntegrityError
from psycopg2 import errorcodes


def sentry_exception_handler(exc, context):
    # Report to sentry if a server error happened.
    if isinstance(exc, APIException) and is_server_error(exc.status_code):
        capture_exception(exc)
    # Call REST framework's default exception handler,
    # to get the standard error response.
    return exception_handler(exc, context)


def is_exception_about_unique_constraint(e: Exception) -> bool:
    """Tells whether an exception is about DB unique constraint violation or not.

    Unfortunately, there is no standard way of detecting such an exception, currently.
    This is a helper function that checks various types of possible exceptions raised, in case of a unique constraint violation.

    This method assumes the DB backend is Postgresql.

    Args:
        e (Exception):

    Returns:
        bool: True if the exception is about unique constraint. False otherwise.
    """
    if isinstance(e, IntegrityError):
        inner_error = e.__cause__
        if not hasattr(inner_error, 'pgcode'):
            raise AssertionError("Unexpected database error! The given exception is of type 'django.db.IntegrityError', "
                                 "but its inner exception is not from psycopg2 (i.e. has no 'pgcode' attribute).")
        return inner_error.pgcode == errorcodes.UNIQUE_VIOLATION
    elif isinstance(e, ValidationError):
        for _, error_details in e.detail.items():
            for error_detail in error_details:
                if 'already exists' in error_detail:
                    return True
    return False
