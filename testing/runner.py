"""Discover and run repository tests, grouped by module and scope."""

import argparse
import contextlib
import importlib.util
import inspect
import io
import json
import sys
import time
import traceback

from datetime import datetime, timezone
from pathlib import Path


# Paths
ROOT = Path(__file__).resolve().parents[1]
RESULTS_PATH = ROOT / "reports" / "results.json"

# Terminal colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run repository tests."
    )

    parser.add_argument(
        "--modules",
        nargs="+",
        metavar="MODULE",
        help="Only run these modules (default: all).",
    )

    return parser.parse_args()


def discover_modules(selected=None):
    """Discover modules from tests/ directories at any depth."""
    modules = {
        ".".join(path.parent.relative_to(ROOT).parts): path
        for path in ROOT.rglob("tests")
        if path.is_dir() and path.parent != ROOT
    }

    if selected:
        unknown = sorted(set(selected) - modules.keys())

        if unknown:
            raise ValueError(
                f"Unknown modules: {', '.join(unknown)}"
            )

        modules = {
            name: modules[name]
            for name in selected
        }

    if not modules:
        raise RuntimeError("No testable modules found.")

    return dict(sorted(modules.items()))


def discover_scopes(tests_directory):
    """Find test_<scope>.py files, excluding nested tests/ directories."""
    scopes = {}

    for path in sorted(tests_directory.rglob("test_*.py")):
        relative_parts = path.relative_to(tests_directory).parts

        # Nested tests/ directories belong to their own modules.
        if "tests" in relative_parts[:-1]:
            continue

        scope = path.stem[len("test_"):]

        if not scope:
            raise ValueError(f"Empty test scope: {path}")

        if scope in scopes:
            raise ValueError(
                f"Duplicate scope {scope!r}: "
                f"{scopes[scope]} and {path}"
            )

        scopes[scope] = path

    if not scopes:
        raise RuntimeError(
            f"No test files found in {tests_directory}"
        )

    return scopes


def load_test_file(path, module_name, scope):
    """Load one test file, keeping repository imports available."""
    import_name = (
        f"_runner_{module_name.replace('.', '_')}_{scope}"
    )

    spec = importlib.util.spec_from_file_location(
        import_name, path
    )

    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load test file: {path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[import_name] = module

    try:
        spec.loader.exec_module(module)

    except Exception:
        sys.modules.pop(import_name, None)
        raise

    return module


def run_test(test_function):
    """Execute a test, capturing its status, duration, and diagnostics."""
    output = io.StringIO()
    started = time.perf_counter()

    try:
        with (
            contextlib.redirect_stdout(output),
            contextlib.redirect_stderr(output),
        ):
            result = test_function()

        if type(result) is not bool:
            raise TypeError(
                "Test must return True or False; "
                f"got {result!r} "
                f"(type: {type(result).__name__})."
            )

        status = "passed" if result else "failed"

    except Exception:
        status = "error"
        output.write(traceback.format_exc())

    duration_ms = round(
        (time.perf_counter() - started) * 1000, 6
    )

    classification = getattr(
        test_function,
        "test_classification",
        "standard",
    )

    return {
        "name": test_function.__name__.removeprefix("test_"),
        "status": status,
        "classification": classification,
        "duration_ms": duration_ms,
        "diagnostics": output.getvalue(),
    }


def run_scope(module_name, scope, path):
    """Run locally defined test functions from a single scope file."""
    test_module = load_test_file(path, module_name, scope)

    functions = [
        function
        for name, function in inspect.getmembers(
            test_module, inspect.isfunction
        )
        if (
            name.startswith("test_")
            and function.__module__ == test_module.__name__
        )
    ]

    if not functions:
        raise RuntimeError(f"No test functions in {path}")

    return {
        "scope": scope,
        "tests": [run_test(function) for function in functions],
    }


def run_module(name, tests_directory):
    """Run every scope and return module results and associated errors."""
    scopes = []
    infrastructure_errors = []

    try:
        discovered_scopes = discover_scopes(tests_directory)

    except Exception:
        infrastructure_errors.append({
            "module": name,
            "scope": None,
            "diagnostics": traceback.format_exc(),
        })
        return {"module": name, "scopes": []}, infrastructure_errors

    for scope, path in discovered_scopes.items():
        try:
            scopes.append(run_scope(name, scope, path))

        except Exception:
            infrastructure_errors.append({
                "module": name,
                "scope": scope,
                "diagnostics": traceback.format_exc(),
            })
            scopes.append({
                "scope": scope,
                "tests": [],
            })

    return {
        "module": name,
        "scopes": scopes,
    }, infrastructure_errors


def write_results(results):
    """Write JSON atomically to avoid leaving partially written output."""
    RESULTS_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = RESULTS_PATH.with_suffix(".json.tmp")

    try:
        temporary.write_text(
            json.dumps(results, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(RESULTS_PATH)

    finally:
        temporary.unlink(missing_ok=True)


def print_summary(results):
    """Print colored test summaries for each module."""
    for module in results["modules"]:
        tests = [
            test
            for scope in module["scopes"]
            for test in scope["tests"]
        ]

        total = len(tests)
        passed = sum(
            test["status"] == "passed"
            for test in tests
        )
        failed = total - passed

        critical_failed = any(
            test["classification"] == "critical"
            and test["status"] != "passed"
            for test in tests
        )

        if critical_failed:
            color = RED
            symbol = "❌"

        elif failed > 0:
            color = YELLOW
            symbol = "⚠️"

        else:
            color = GREEN
            symbol = "✔"

        print(
            f"{color}{symbol} {module['module']}: "
            f"{passed}/{total} passed{RESET}"
        )


def main():
    """Discover, execute, save, and summarize repository tests."""
    args = parse_args()

    results = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "complete": False,
        "modules": [],
        "infrastructure_errors": [],
    }

    try:
        modules = discover_modules(args.modules)

        for name, path in modules.items():
            module_results, errors = run_module(name, path)
            results["modules"].append(module_results)
            results["infrastructure_errors"].extend(errors)

        results["complete"] = not results["infrastructure_errors"]

    except Exception:
        results["infrastructure_errors"].append({
            "module": None,
            "scope": None,
            "diagnostics": traceback.format_exc(),
        })

    try:
        write_results(results)

    except Exception:
        print(
            "Could not write test results:\n"
            + traceback.format_exc(),
            file=sys.stderr,
        )
        return 2

    print_summary(results)

    if not results["complete"]:
        print(
            "Test run incomplete; see infrastructure_errors "
            "in results.json",
            file=sys.stderr,
        )
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
