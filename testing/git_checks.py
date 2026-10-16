"""Local Git hooks: generate commit reports and validate pushes to main."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ZERO_OID = "0" * 40


def git(*args, cwd=ROOT, input_text=None, check=True):
    return subprocess.run(
        ["git", *args], cwd=cwd, input=input_text, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=check,
    )


def run_python(module, cwd):
    return subprocess.run([sys.executable, "-m", module], cwd=cwd).returncode


def load_results(root):
    with (root / "reports" / "results.json").open(encoding="utf-8") as file:
        return json.load(file)


def critical_failures(results):
    return [
        f"{module['module']}/{scope['scope']}/{test['name']} ({test['status']})"
        for module in results.get("modules", [])
        for scope in module.get("scopes", [])
        for test in scope.get("tests", [])
        if test.get("classification") == "critical" and test.get("status") != "passed"
    ]


def validate_results(root):
    results = load_results(root)
    if not results.get("complete") or results.get("infrastructure_errors"):
        raise RuntimeError("Test run incomplete; inspect reports/results.json")
    modules = results.get("modules", [])
    if not modules or not any(scope.get("tests") for module in modules for scope in module.get("scopes", [])):
        raise RuntimeError("No tests executed")
    failures = critical_failures(results)
    if failures:
        raise RuntimeError("Critical tests failed:\n  " + "\n  ".join(failures))
    return results


def report_paths(results):
    paths = ["README.md", "reports/results.json", "reports/assets/dashboard.svg"]
    for module in results["modules"]:
        name = module["module"]
        paths.extend([f"reports/{name}.md", f"reports/assets/{name}.svg"])
    return paths


def pre_commit():
    print("\nStrategyEngine | pre-commit: tests and reports", flush=True)
    # Testing the worktree while committing the index is unsafe if tracked changes
    # are unstaged. Reject rather than silently report on the wrong code.
    if git("diff", "--quiet", check=False).returncode != 0:
        raise RuntimeError("Unstaged tracked changes detected. Stage or discard them before committing.")
    # New untracked Python files could also affect discovery/imports.
    untracked = git("ls-files", "--others", "--exclude-standard", "-z").stdout.split("\0")
    untracked_sources = [p for p in untracked if p.endswith(".py")]
    if untracked_sources:
        raise RuntimeError("Untracked Python files must be staged first: " + ", ".join(untracked_sources))

    runner_code = run_python("testing.runner", ROOT)
    if runner_code not in (0, 2):
        raise RuntimeError(f"Runner crashed (exit {runner_code})")
    results = load_results(ROOT)
    # A runner infrastructure error blocks the commit; test failures do not.
    if runner_code == 2 or not results.get("complete"):
        raise RuntimeError("Test infrastructure failed; see reports/results.json")
    if run_python("testing.report_writer", ROOT) != 0:
        raise RuntimeError("Report generation failed")
    paths = report_paths(results)
    git("add", "--", *paths)
    failures = critical_failures(results)
    if failures:
        print("WARNING: critical test failures (commit still allowed):", flush=True)
        for failure in failures:
            print("  " + failure, flush=True)
    print("Reports staged; commit permitted.", flush=True)


def validate_commit(oid):
    with tempfile.TemporaryDirectory(prefix="strategyengine-push-") as temporary:
        checkout = Path(temporary) / "checkout"
        git("worktree", "add", "--detach", "--", str(checkout), oid)
        try:
            if run_python("testing.runner", checkout) != 0:
                raise RuntimeError("Runner failed in proposed main commit")
            validate_results(checkout)
            if run_python("testing.report_writer", checkout) != 0:
                raise RuntimeError("Report writer failed in proposed main commit")
        finally:
            git("worktree", "remove", "--force", "--", str(checkout))


def pre_push():
    print("\nStrategyEngine | pre-push: checking destination refs", flush=True)
    # stdin: <local-ref> <local-oid> <remote-ref> <remote-oid>
    updates = [line.split() for line in sys.stdin if line.strip()]
    main_updates = [fields for fields in updates if len(fields) == 4 and fields[2] == "refs/heads/main"]
    if not main_updates:
        print("No main update; push permitted.", flush=True)
        return
    for local_ref, local_oid, remote_ref, remote_oid in main_updates:
        if set(local_oid) == {"0"}:
            raise RuntimeError("Deleting remote main is prohibited")
        if set(remote_oid) != {"0"}:
            ancestry = git("merge-base", "--is-ancestor", remote_oid, local_oid, check=False)
            if ancestry.returncode != 0:
                raise RuntimeError("Non-fast-forward updates to main are prohibited")
        print(f"Validating proposed main commit {local_oid[:12]}...", flush=True)
        validate_commit(local_oid)
    print("Critical tests passed; push permitted.", flush=True)


def main():
    try:
        if len(sys.argv) != 2 or sys.argv[1] not in ("pre-commit", "pre-push"):
            raise RuntimeError("Usage: python -m testing.git_checks {pre-commit|pre-push}")
        if sys.argv[1] == "pre-commit":
            pre_commit()
        else:
            pre_push()
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError, RuntimeError, KeyError, json.JSONDecodeError) as error:
        print(f"\nHOOK BLOCKED: {error}", file=sys.stderr)
        if isinstance(error, subprocess.CalledProcessError) and error.stderr:
            print(error.stderr, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
