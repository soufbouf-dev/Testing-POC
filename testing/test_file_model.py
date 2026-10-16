"""Reference structure for StrategyEngine test files.

Copy the relevant patterns into a module's tests/ directory.
- Name tests test_<descriptive_behavior>.
- Return True for a pass, False for an expected comparison failure.
- Let unexpected exceptions propagate so the runner records an error.
- Use @critical only for tests that must pass before changes enter main.
- Tests without @critical are standard by default.
- Do not execute tests or generate reports in this file.
"""

from testing.helpers import critical


@critical
def test_important_behavior():
    """Example of a critical test."""
    actual = 2 + 2
    expected = 4
    if actual != expected:
        print(f"Expected {expected}, got {actual}")
        return False
    return True


def test_standard_behavior():
    """Example of a standard test."""
    actual = "strategy".upper()
    expected = "STRATEGY"
    if actual != expected:
        print(f"Expected {expected!r}, got {actual!r}")
        return False
    return True

