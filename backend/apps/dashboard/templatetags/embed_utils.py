import base64
import mimetypes
from django import template
from django.contrib.staticfiles.finders import find as find_static_file

register = template.Library()


@register.simple_tag
def encode_file_to_base64(path):
    """
    A template tag that returns a encoded string representation of a file.
    You can embed your files in templates by this tag.
    Usage:
        {% encode_file_to_base64 path %}
    Examples:
        <img src="{% encode_file_to_base64 'path/to/img.png' %}">
    """
    file_path = find_static_file(path)
    if file_path is None:
        raise FileNotFoundError(f"Path {path} not found in static folders.")

    file_mime_type = get_mime_type(file_path)
    file_data_base64 = get_base64(get_data(file_path))
    return f"data:{file_mime_type};base64,{file_data_base64}"


def get_data(file_path) -> bytes:
    with open(file_path, 'rb') as file:
        return file.read()


def get_base64(data: bytes) -> str:
    return base64.b64encode(data).decode('ascii')


def get_mime_type(file_path) -> str:
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type
