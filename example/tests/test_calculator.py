from testing.helpers import critical, compare
from example.calculator import (
    add,
    subtract,
    multiply,
    divide,
)

@critical
def test_add():
    a = 1.0
    b = 2.1
    expected = 3.15
    actual = round(add(a, b), 2)
    return compare(actual, expected)

@critical
def test_subtract():
    a = 1.0
    b = 2.1
    expected = -1.10
    actual = round(subtract(a, b), 2)
    return compare(actual, expected)

@critical
def test_multiply():
    a = 5.0
    b = 2.1
    expected = 10.50
    actual = round(multiply(a, b), 2)
    return compare(actual, expected)

@critical
def test_multiply_negative():
    a = 5.0
    b = -2.1
    expected = -10.50
    actual = round(multiply(a, b), 2)
    return compare(actual, expected)

@critical
def test_divide():
    a = 5.0
    b = 2.1
    expected = 2.38
    actual = round(divide(a, b), 2)
    return compare(actual, expected)

@critical
def test_divide_negative():
    a = -5.0
    b = 2.1
    expected = -2.38
    actual = round(divide(a, b), 2)
    return compare(actual, expected)

@critical
def test_divide_by_zero():
    a = -5.0
    b = 0.0
    try:
        _ = divide(a, b)
        return False
    except ZeroDivisionError:
        return True