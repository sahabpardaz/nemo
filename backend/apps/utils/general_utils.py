from typing import List, Tuple, Union, Dict, Any, Iterable, Optional
import itertools
from datetime import date, datetime, time, timedelta
from collections import Counter
import pytz


def coalesce(*args):
    """Returns the first argument which is not None."""
    for el in args:
        if el is not None:
            return el
    return None


JSONValueType = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]
JSONType = Union[Dict[str, JSONValueType], List[JSONValueType]]

StringTuple = Tuple[str, ...]
MultipleStrings = Union[str, List[str], StringTuple]


def convert_names_to_tuple(names: MultipleStrings, tuple_name: str) -> StringTuple:
    """
    Converts a single-unit/list/tuple of names (strings) to a tuple.

    It is naturally used to provide convenience when calling functions which need a tuple of strings.
    Consider a function `f(names)`.
    All the following forms of calling `f` is valid
     if we put `names = convert_names_to_tuple(names)` in the first line of its implementation:
    f('a')         --> f(('a',))
    f(('a',))      --> f(('a',))
    f(['a',])      --> f(('a',))
    f(('a','b'))   --> f(('a','b'))
    f(['a','b'])   --> f(('a','b'))

    Parameters:
        names (MultipleStrings): The single-unit/list/tuple of strings
        tuple_name (str): Name of the tuple (used in the error message)

    Returns:
        (StringTuple): The unified tuple
    """
    if isinstance(names, tuple):
        return names
    if isinstance(names, list):
        return list(names)
    if isinstance(names, str):
        return (names,)
    raise TypeError(f"Type of {tuple_name} must be str, tuple[str], or list[str]")


def truncated_to_str(items: Iterable, max_len: int, quotation: Optional[str] = None) -> str:
    """
    Truncates a list/iterable to size `max_len`, and then converts it to string.
    If the list is truncated, the string is followed by ellipsis.
    List items are quoted by `quotation` (if any).
    """
    if items is None:
        items = []
    max_len = max(max_len, 1)
    if quotation is None:
        quotation = ""
    return (
        ", ".join(f"{quotation}{item}{quotation}" for item in itertools.islice(items, max_len))
        + (", ..." if len(items) > max_len else "")
    )


def find_duplicate_object_values_by_fields(items: Iterable, fields: MultipleStrings) -> Dict[Tuple, int]:
    """
    Finds duplicate values in a list (iterable) of objects when projected to a subset of fields.

    Only values of the given fields are looked for duplication.
    Consider the given fields are ('a', 'b').
    Objects (a=1, b=2, c=3) and (a=1, b=2, c=4) are considered the same.
    But they are different from (a=1, b=3) or (a=2, b=2, c=3).
    If a given field is not present in an object, it is considered to be None.

    Parameters:
        items (List): List of items to look for duplicate values
        fields (MultipleStrings): The set of fields probed for duplicate values

    Returns:
        Dict[Tuple, int]: Duplicate values in the list of items together with the number of their occurrence in the list.
                            The values in each tuple is in the same order as the order specified in the parameter `fields`.
    """
    fields = convert_names_to_tuple(fields, "fields")
    counter = Counter(tuple(getattr(item, field, None) for field in fields) for item in items)
    return {values: cnt for (values, cnt) in counter.most_common() if cnt > 1}


def find_duplicate_dict_values_by_keys(items: Iterable[Dict], keys: MultipleStrings) -> Dict[Tuple, int]:
    """
    Finds duplicate values in a list (iterable) of dictionaries when projected to a subset of keys.

    Only values of the given keys are looked up for duplication.
    Consider the given keys are ('a', 'b').
    Dictionaries {'a'=1, 'b'=2, 'c'=3} and {'a'=1, 'b'=2, 'c'=4} are considered the same.
    But they are different from {'a'=1, 'b'=3} or {'a'=2, 'b'=2, 'c'=3}.
    If a given key is not present in a dictionary, it is considered to be None.

    Parameters:
        items (List[Dict]): List of items to look for duplicate values
        keys (MultipleStrings): The set of keys probed for duplicate values

    Returns:
        Dict[Tuple, int]: Duplicate values in the list of items together with the number of their occurrence in the list.
                            The values in each tuple is in the same order as the order specified in the parameter `keys`.
    """
    keys = convert_names_to_tuple(keys, "keys")
    counter = Counter(tuple(item.get(key, None) for key in keys) for item in items)
    return {values: cnt for (values, cnt) in counter.most_common() if cnt > 1}


def add_seconds(time: datetime, seconds: int):
    return time + timedelta(seconds=seconds)


def convert_date_to_datetime(d: date, t: time = time.min.replace(tzinfo=pytz.utc)) -> datetime:
    """Adds a time to the given date.

    Args:
        d (date):
        t (time): default 00:00 UTC
    """
    return datetime.combine(d, t)
