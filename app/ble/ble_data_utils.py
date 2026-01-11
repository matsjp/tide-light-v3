"""
BLE Data Utilities for Pybleno.

Helper functions for converting between Python values and byte arrays
used by pybleno characteristics.
"""

import array
from pybleno import readUInt8, writeUInt8


def string_to_bytes(text: str) -> array.array:
    """
    Convert a string to a byte array for BLE transmission.
    
    Args:
        text: String to convert
    
    Returns:
        array.array('B') containing UTF-8 encoded bytes
    """
    data = array.array('B', [0] * len(text))
    for i in range(len(text)):
        writeUInt8(data, ord(text[i]), i)
    return data


def bytes_to_string(data: array.array) -> str:
    """
    Convert a byte array from BLE to a string.
    
    Args:
        data: array.array('B') containing UTF-8 bytes
    
    Returns:
        Decoded string
    """
    result = ''
    for i in range(len(data)):
        result += chr(readUInt8(data, i))
    return result


def uint8_to_bytes(value: int) -> array.array:
    """
    Convert a single uint8 value to a byte array.
    
    Args:
        value: Integer 0-255
    
    Returns:
        array.array('B') with single byte
    """
    data = array.array('B', [0] * 1)
    writeUInt8(data, value, 0)
    return data


def bytes_to_uint8(data: array.array) -> int:
    """
    Extract a uint8 value from a byte array.
    
    Args:
        data: array.array('B') with at least 1 byte
    
    Returns:
        Integer value 0-255
    """
    return readUInt8(data, 0)


def json_to_bytes(json_str: str) -> array.array:
    """
    Convert a JSON string to a byte array.
    Same as string_to_bytes but semantically clearer.
    
    Args:
        json_str: JSON string to convert
    
    Returns:
        array.array('B') containing UTF-8 encoded bytes
    """
    return string_to_bytes(json_str)


def bytes_to_json(data: array.array) -> str:
    """
    Convert a byte array to a JSON string.
    Same as bytes_to_string but semantically clearer.
    
    Args:
        data: array.array('B') containing UTF-8 bytes
    
    Returns:
        JSON string
    """
    return bytes_to_string(data)
