from testing.helpers import critical, compare
from example.calculator import (
    format_result,
    operation_label,
)



def test_format_result():
    value = 2.154
    decimal_places = 2
    expected = "2.15"
    actual = format_result(value, decimal_places)
    return compare(actual, expected)

def test_format_round_up():
    # meant to fail because round up is not handled by function
    value = 2.156
    decimal_places = 2
    expected = "2.15"
    actual = format_result(value, decimal_places)
    return compare(actual, expected)

def test_operation_label():
    # meant to fail on purpose due to typo, raises error
    operation = "addy"
    expected = "Addition"
    actual = operation_label(operation)
    return compare(actual, expected)

def test_operation_label_error():
    operation = "addy"
    try:
        operation_label(operation)
        return False
    except ValueError:
        return True