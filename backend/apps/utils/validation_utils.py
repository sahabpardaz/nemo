from typing import Tuple, Dict, Iterable, Callable
from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework.fields import empty

from apps.utils.general_utils import MultipleStrings, find_duplicate_dict_values_by_keys, truncated_to_str


def validate_percentage(value):
    try:
        value = float(value)
    except ValueError:
        raise ValidationError(f"Value '{value}' is not a floating number.")
    if not (0 <= value <= 100):
        raise ValidationError(
            'Percentage value should be between 0 and 100.')
    return value


def default_error_message_builder_for_duplicate_values_in_unique_fields(
    keys: MultipleStrings,
    duplicate_values: Dict[Tuple, int],
) -> str:
    return f"Duplicate values for {keys}: {truncated_to_str(duplicate_values.keys(), 3)}"


def check_for_duplicate_values_in_unique_fields(
    items: Iterable[Dict],
    keys: MultipleStrings,
    message_builder: Callable[[MultipleStrings, Dict[Tuple, int]], str]
    = default_error_message_builder_for_duplicate_values_in_unique_fields,
) -> None:
    """
    Checks if there are duplicate values in a list (iterable) of data (during validation).
    If there are duplicate a ValidationError with a proper error message is raised.
    The error message is built by the `message_builder`.
    """
    duplicate_values = find_duplicate_dict_values_by_keys(items, keys)
    if duplicate_values:
        raise serializers.ValidationError(message_builder(keys, duplicate_values))


class InconsistentDataError(Exception):
    def __init__(self, description: str) -> None:
        super().__init__(f"Inconsistent data error: {description}")


class SerializerValidateAndSaveMixin:
    """Packs Validation and Save processes in a Serializer together as a class method.
    """

    @classmethod
    def validate_and_save(cls, instance=None, data=empty, **kwargs):
        """Validates instance or data and saves it

        Args:
            instance (cls, optional): Instance object to be saved. Defaults to None.
            data (dict, optional): Data, as a dict, to be saved. Defaults to empty.

        Raises:
            serializers.ValidationError: When validation fails.
        """
        if (instance is None and data is empty) or (instance is not None and data is not empty):
            raise ValueError('Exactly one of instance or data args should be specified.')
        data_to_save = data
        if data_to_save is empty:
            data_to_save = cls(instance).data

        serializer = cls(data=data_to_save, **kwargs)
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
        except Exception as e:
            cls._handle_save_error(e, instance, data, **kwargs)

    @classmethod
    def _handle_save_error(cls, e: Exception, instance=None, data=empty, **kwargs):
        """A handler for catching the errors of save during validate_and_save method. It can be overriden by child classes.

        Args:
            e (Exception): The raised exception
        """
        raise e
