"""Small calculator module for practicing StrategyEngine tests.

The functions intentionally contain no test or reporting logic.
"""


def add(a: float, b: float) -> float:
    """Return the sum of two numbers."""
    return a + b


def subtract(a: float, b: float) -> float:
    """Return the difference between two numbers."""
    return a - b


def multiply(a: float, b: float) -> float:
    """Return the product of two numbers."""
    return a * b


def divide(a: float, b: float) -> float:
    """Return a divided by b.

    Raises:
        ZeroDivisionError: If b is zero.
    """
    if b == 0:
        raise ZeroDivisionError("Cannot divide by zero")
    return a / b


def format_result(value: float, decimal_places: int = 2) -> str:
    """Return a number formatted to the requested decimal places."""
    return f"{value:.{decimal_places}f}"


def operation_label(operation: str) -> str:
    """Return a readable label for a supported operation.

    Raises:
        ValueError: If the operation is not supported.
    """
    labels = {
        "add": "Addition",
        "subtract": "Subtraction",
        "multiply": "Multiplication",
        "divide": "Division",
    }
    if operation not in labels:
        raise ValueError(f"Unknown operation: {operation}")
    return labels[operation]