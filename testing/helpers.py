"""Shared testing utilities for StrategyEngine."""
import pandas as pd


def critical(test_function):
    """Mark a test as critical. Undecorated tests are standard."""
    test_function.test_classification = "critical"
    return test_function


# Register type-specific comparison functions here when needed.
def compare_dataframes(actual, expected):
    """Compare two DataFrames and display detailed differences."""

    try:
        pd.testing.assert_frame_equal(actual, expected)
        return True

    except AssertionError as e:
        print(f"DataFrame mismatch:\n{e}")
        return False
    
    
COMPARATORS = {
    pd.DataFrame: compare_dataframes
}


def compare(actual, expected):
    """
    Compare two values and print diagnostics when they differ.

    - Types must match exactly.
    - Registered types use their custom comparator.
    - Other types use ordinary equality.
    - Returns True or False.
    - Unexpected comparison errors propagate to the test runner.
    """

    # Check types first.
    if type(actual) is not type(expected):
        print(
            f"Type mismatch: expected {type(expected).__name__}, "
            f"got {type(actual).__name__}"
        )
        return False

    # Use a specialized comparator when one is registered.
    comparator = COMPARATORS.get(type(actual))

    if comparator is not None:
        return comparator(actual, expected)

    # Default comparison.
    result = actual == expected

    if not isinstance(result, bool):
        raise TypeError(
            f"Comparison for {type(actual).__name__} "
            "did not return a boolean. "
            "A specialized comparator may be required."
        )

    if not result:
        print(
            f"Expected: {expected!r}\n"
            f"Actual:   {actual!r}"
        )

    return result
