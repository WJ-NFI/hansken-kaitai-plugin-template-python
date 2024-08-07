import enum
import inspect
import json
from io import BufferedWriter
from typing import Any, BinaryIO, Dict, Generator, List, Type

import kaitaistruct
from kaitaistruct import KaitaiStruct
from json_stream import streamable_dict, streamable_list


def write_to_json(data_binary: BinaryIO, writer: BufferedWriter, class_type: Type[KaitaiStruct]):
    """
    Writes a binary form of JSON string into a BufferedWriter

    @param data_binary: binary data containing the file content
    @param writer: bufferedWriter to write the binary form of the JSON string to
    @param class_type: class that contains the parsing to a KaiTai struct
    @return: JSON string representing contents of data object
    """
    writer.write(bytes(to_json_string(data_binary, class_type), "utf-8"))


def to_json_string(data_binary: BinaryIO, class_type: Type[KaitaiStruct]) -> str:
    """
    Parses a binary data object to a JSON string

    @param data_binary: binary data containing the file content
    @param class_type: class that contains the parsing to a KaiTai struct
    @return: JSON string representing contents of data object
    """
    parsed_kaitai_struct = class_type.from_io(data_binary)
    return json.dumps(_object_to_dict(parsed_kaitai_struct), indent=2)


@streamable_dict
def _object_to_dict(instance: Any) -> Generator[Dict[str, Any], None, None]:
    """
    Recursive helper method that parses an object to a dictionary.
    Key: The parameters and property method names
    Value: The parsed value or returning values of the fields and property method names

    @param instance: object that needs parsing to dictionary
    @yield: dictionary containing parsed fields and their respective parsed values in a dictionary
    """
    parameters_dict = _parameters_dict(instance)
    for key, value_object in parameters_dict.items():
        if not key.startswith("_") and value_object is not None:
            if _is_kaitai_struct(value_object):
                yield _to_lower_camel_case(key), _object_to_dict(value_object)
            elif _is_list(value_object):
                yield _to_lower_camel_case(key), _list_to_dict(value_object)
            else:
                yield _to_lower_camel_case(key), _process_value(value_object)


def _parameters_dict(instance: Any) -> Dict[str, Any]:
    """
    Helper method that parses an object to a dictionary.
    Key: The parameters and property method names
    Value: The original value or returning values of the original fields and property method names

    @param instance: object that needs parsing to dictionary
    @yield: dictionary containing original field names and their respective values in a dictionary
    """
    parameters_dict = vars(instance)
    if _is_kaitai_struct(instance):
        methods = _get_property_methods(type(instance))
        for method in methods:
            parameters_dict[str(method)] = getattr(instance, method)
    return parameters_dict


def _process_value(value_object: Any) -> Any:
    """
    Helper method to process the different types of values to enable their printing in a json

    @param value_object: value of whatever type that might require preprocessing; if not, the value itself is returned
    @return: type that can be dumped in a json
    """
    if type(value_object) is bytes:
        return list(value_object)
    if isinstance(value_object, enum.Enum):
        return {
            "name": value_object.name.upper(),
            "value": value_object.value
        }
    return value_object


def _get_property_methods(class_type: Any) -> List[str]:
    """
    Helper method to obtain method names in a class that are annotated with @property

    @param class_type: class_type that the method obtains @property method names from
    @return: list of method names containing the annotation property
    """
    property_method_names = []
    for name, member in inspect.getmembers(class_type):
        if isinstance(member, property):
            property_method_names.append(name)
    return property_method_names


def _is_kaitai_struct(value_object: Any) -> bool:
    return issubclass(type(value_object), kaitaistruct.KaitaiStruct)


def _is_list(value_object: Any) -> bool:
    return issubclass(type(value_object), List)


@streamable_list
def _list_to_dict(object_list: List[Any]) -> Generator[tuple[str, Any], None, None]:
    for obj in object_list:
        yield _object_to_dict(obj)


def _to_camel_case(snake_str: str) -> str:
    return "".join(x.capitalize() for x in snake_str.lower().split("_"))


def _to_lower_camel_case(snake_str: str) -> str:
    camel_string = _to_camel_case(snake_str)
    return snake_str[0].lower() + camel_string[1:]
