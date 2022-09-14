from typing import Type, Union, List, Dict, Any
from django.core.management.base import CommandError
from rest_framework.parsers import JSONParser
from rest_framework.exceptions import ParseError
from rest_framework.serializers import BaseSerializer
from apps.utils.general_utils import JSONType


SerializerClass = Type[BaseSerializer]
AddedInstancesType = Union[List[Any], Dict[str, Any]]


def read_json_file(file_path: str) -> JSONType:
    with open(file_path, "rb") as f:
        try:
            return JSONParser().parse(f)
        except ParseError as e:
            raise CommandError(f"Invalid json format in file '{file_path}':\n{e}")


def add_json_instances(json_data: JSONType, serializer_class: SerializerClass, data_path: str) -> AddedInstancesType:
    if isinstance(json_data, list):
        serializer = serializer_class(data=json_data, many=True)
        if not serializer.is_valid():
            raise CommandError(f"Invalid data in file '{data_path}':\n{serializer.errors}")
        return serializer.create(serializer.validated_data)
    elif isinstance(json_data, dict):
        errors = dict()
        instances = dict()
        for instance_key, instance_data in json_data.items():
            serializer = serializer_class(data=instance_data, many=False)
            if not serializer.is_valid():
                errors[instance_key] = serializer.errors
            else:
                instances[instance_key] = serializer.create(serializer.validated_data)
        if errors:
            raise CommandError(f"Invalid data in file '{data_path}':\n{errors}")
        return instances
    else:
        raise CommandError(f"Invalid data in file '{data_path}': Not a dict or array.")


def add_json_file_instances(file_path: str, serializer_class: SerializerClass) -> AddedInstancesType:
    return add_json_instances(
        json_data=read_json_file(file_path),
        serializer_class=serializer_class,
        data_path=file_path
    )
