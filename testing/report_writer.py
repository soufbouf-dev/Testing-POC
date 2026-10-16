"""Generate GitHub-friendly module reports and a README testing dashboard."""

import argparse
import html
import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS_PATH = ROOT / "reports" / "results.json"
REPORTS_DIRECTORY = ROOT / "reports"
README_PATH = ROOT / "README.md"

DASHBOARD_START = "<!-- TESTING_DASHBOARD_START -->"
DASHBOARD_END = "<!-- TESTING_DASHBOARD_END -->"

STATUS_LABELS = {
    "passed": "✅ Passed",
    "failed": "❌ Failed",
    "error": "💥 Error",
    "skipped": "⏭️ Skipped",
}


def parse_args():
    """Read optional command-line switches."""
    parser = argparse.ArgumentParser(description="Generate test reports from JSON.")
    parser.add_argument(
        "--skip-readme",
        action="store_true",
        help="Generate module reports without updating the README dashboard.",
    )
    return parser.parse_args()


def load_results():
    """Load the JSON results produced by the runner."""
    with RESULTS_PATH.open(encoding="utf-8") as file:
        return json.load(file)


def module_tests(module):
    """Collect tests from every scope of a module."""
    return [test for scope in module["scopes"] for test in scope["tests"]]


def summarize(tests):
    """Calculate status counts and critical-test coverage."""
    total = len(tests)
    passed = sum(test["status"] == "passed" for test in tests)
    failed = sum(test["status"] == "failed" for test in tests)
    errors = sum(test["status"] == "error" for test in tests)
    skipped = sum(test["status"] == "skipped" for test in tests)
    critical = [test for test in tests if test["classification"] == "critical"]
    critical_passed = sum(test["status"] == "passed" for test in critical)
    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "skipped": skipped,
        "critical_total": len(critical),
        "critical_passed": critical_passed,
        "rate": 100 * passed / total if total else 0.0,
    }


def status_info(summary, complete=True):
    """Return the overall label, icon, and badge color."""
    if not complete:
        return "Incomplete run", "⛔", "red"
    if summary["critical_passed"] < summary["critical_total"]:
        return "Critical failures", "❌", "red"
    if summary["total"] == 0:
        return "No tests", "⚠️", "yellow"
    if summary["passed"] < summary["total"]:
        return "Standard failures", "⚠️", "yellow"
    return "All tests passed", "✅", "brightgreen"


def svg_escape(value):
    """Escape untrusted labels for SVG text nodes."""
    return html.escape(str(value), quote=True)


def svg_text(x, y, value, size=14, color="#cbd5e1", weight=400, anchor=None):
    anchor_attr = f' text-anchor="{anchor}"' if anchor else ""
    return (f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" '
            f'font-weight="{weight}"{anchor_attr}>{svg_escape(value)}</text>')


def svg_rect(x, y, width, height, fill, radius=0):
    return (f'<rect x="{x}" y="{y}" width="{width}" height="{height}" '
            f'rx="{radius}" fill="{fill}"/>')


def svg_status(summary, complete=True):
    label, _, _ = status_info(summary, complete)
    if not complete or summary["critical_passed"] < summary["critical_total"]:
        return label, "#fb7185"
    if summary["total"] == 0 or summary["passed"] < summary["total"]:
        return label, "#fbbf24"
    return label, "#4ade80"


def render_svg(title, summary, timestamp, rows=None, complete=True):
    """Render a self-contained GitHub-compatible SVG with an opaque dark canvas."""
    rows = rows or []
    width = 960
    height = 290 + (len(rows) * 54 if rows else 0)
    label, accent = svg_status(summary, complete)
    total = summary["total"]
    rate = summary["rate"]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="{svg_escape(title)}: {summary["passed"]} of {total} tests passed">',
        '<style>text{font-family:Arial,Helvetica,sans-serif}</style>',
        svg_rect(0, 0, width, height, "#0f172a", 18),
        svg_rect(0, 0, 6, height, accent, 3),
        svg_text(32, 42, title.upper(), 15, "#94a3b8", 700),
        svg_text(32, 88, f'{rate:.1f}%', 46, "#f8fafc", 700),
        svg_text(210, 84, label, 18, accent, 700),
        svg_text(210, 108, f'{summary["passed"]} / {total} tests passed', 14),
        svg_text(928, 40, format_timestamp(timestamp), 12, "#94a3b8", anchor="end"),
        svg_rect(32, 128, 896, 12, "#334155", 6),
        svg_rect(32, 128, round(896 * rate / 100, 2), 12, accent, 6),
    ]
    metrics = [
        ("PASSED", str(summary["passed"]), "#4ade80"),
        ("FAILED", str(summary["failed"]), "#fb7185"),
        ("ERRORS", str(summary["errors"]), "#fb7185"),
        ("CRITICAL", f'{summary["critical_passed"]}/{summary["critical_total"]}',
         "#4ade80" if summary["critical_passed"] == summary["critical_total"] else "#fb7185"),
    ]
    for index, (name, value, color) in enumerate(metrics):
        x = 32 + index * 228
        parts.extend([
            svg_rect(x, 160, 212, 76, "#1e293b", 10),
            svg_text(x + 16, 186, name, 12, "#94a3b8", 700),
            svg_text(x + 16, 218, value, 27, color, 700),
        ])
    if rows:
        parts.append(svg_text(32, 269, "BREAKDOWN", 12, "#94a3b8", 700))
        for index, (name, counts) in enumerate(rows):
            y = 280 + index * 54
            _, row_color = svg_status(counts)
            parts.extend([
                svg_rect(32, y, 896, 46, "#1e293b", 8),
                svg_rect(46, y + 12, 4, 22, row_color, 2),
                svg_text(64, y + 29, name[:48], 15, "#f8fafc", 600),
                svg_text(720, y + 29, f'{counts["passed"]}/{counts["total"]} passed', 14, "#cbd5e1", anchor="end"),
                svg_rect(750, y + 18, 120, 10, "#334155", 5),
                svg_rect(750, y + 18, round(120 * counts["rate"] / 100, 2), 10, row_color, 5),
                svg_text(914, y + 29, f'{counts["rate"]:.0f}%', 13, row_color, 700, "end"),
            ])
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def markdown_cell(value):
    """Escape text for GitHub Markdown table cells."""
    return str(value).replace("|", "\\|").replace("\n", " ")


def html_text(value):
    """Escape text used in HTML summary elements."""
    import html
    return html.escape(str(value), quote=True)


def diagnostics_block(value):
    """Fence diagnostics without conflicts with embedded backticks."""
    value = value.rstrip() or "(No diagnostics provided)"
    longest = max((len(match.group()) for match in re.finditer(r"`+", value)), default=0)
    fence = "`" * max(3, longest + 1)
    return f"{fence}text\n{value}\n{fence}"


def format_timestamp(timestamp):
    """Format an ISO timestamp for report display."""
    parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    return parsed.strftime("%d %b %Y · %H:%M UTC")


def progress_bar(summary, width=12):
    """Build a text-only pass-rate bar that works on GitHub."""
    filled = round(width * summary["passed"] / summary["total"]) if summary["total"] else 0
    return "🟩" * filled + "⬜" * (width - filled)


def scope_heading(scope):
    """Make machine-readable scope names friendlier to read."""
    return scope.replace("_", " ").title()


def build_module_report(module, timestamp, complete=True):
    """Render module details beneath its SVG visual summary."""
    name = module["module"]
    summary = summarize(module_tests(module))
    lines = [
        f"# {name} · Test Report",
        "",
        "[← Testing dashboard](../README.md#testing-dashboard)",
        "",
        f"![{markdown_cell(name)} test summary](assets/{name}.svg)",
        "",
    ]
    for scope in module["scopes"]:
        counts = summarize(scope["tests"])
        _, icon, _ = status_info(counts)
        lines.extend([
            "", "---", "",
            f"## {icon} {scope_heading(scope['scope'])}",
            "",
            f"**{counts['passed']}/{counts['total']} passed** · {counts['rate']:.1f}%",
            "",
            "| Test | Priority | Result | Time |",
            "|:---|:---:|:---:|---:|",
        ])
        for test in scope["tests"]:
            priority = "Critical" if test["classification"] == "critical" else "Standard"
            result = STATUS_LABELS.get(test["status"], test["status"])
            lines.append(
                f"| `{markdown_cell(test['name'])}` | {priority} | "
                f"{markdown_cell(result)} | {test['duration_ms']:.4f} ms |"
            )
        problematic = [test for test in scope["tests"] if test["status"] in ("failed", "error")]
        if problematic:
            lines.extend(["", "### Failure diagnostics", ""])
            for test in problematic:
                label = STATUS_LABELS.get(test["status"], test["status"])
                lines.extend([
                    "<details>",
                    f"<summary><strong>{html_text(label)} · {html_text(test['name'])}</strong></summary>",
                    "", diagnostics_block(test.get("diagnostics", "")), "", "</details>", "",
                ])
    lines.extend(["", "---", "", "<sub>Generated from <code>reports/results.json</code>.</sub>"])
    return "\n".join(lines) + "\n"


def build_dashboard(results):
    """Render the README SVG dashboard with unobtrusive links to details."""
    modules = results["modules"]
    lines = [
        "![Repository testing dashboard](reports/assets/dashboard.svg)", "",
    ]
    if len(modules) == 1:
        name = modules[0]["module"]
        lines.append(
            f"🔎 **For the full breakdown** "
            f"[explore the {name} test report →](reports/{name}.md)"
        )
    elif modules:
        links = " · ".join(
            f"[{module['module']} →](reports/{module['module']}.md)"
            for module in modules
        )
        lines.extend(["🔎 **Dive into the detailed test reports**", "", links])
    if not results.get("complete", False):
        lines.extend(["", "> ⚠️ Run incomplete. See `infrastructure_errors` in `reports/results.json`."])
    lines.extend(["", "<sub>Generated automatically from the latest test run.</sub>"])
    return "\n".join(lines)


def update_readme(dashboard):
    """Replace only the marked dashboard section, or append it if missing."""
    original = README_PATH.read_text(encoding="utf-8") if README_PATH.exists() else ""

    start = original.find(DASHBOARD_START)
    end = original.find(DASHBOARD_END)

    if (start == -1) != (end == -1):
        raise ValueError("README has only one testing dashboard marker.")
    if start != -1 and end < start:
        raise ValueError("README testing dashboard markers are out of order.")

    section = f"{DASHBOARD_START}\n\n{dashboard}\n\n{DASHBOARD_END}"

    if start != -1:
        updated = (
            original[:start]
            + section
            + original[end + len(DASHBOARD_END):]
        )

    else:
        title = "## Testing Dashboard"
        title_pos = original.find(title)

        if title_pos != -1:
            insert_pos = title_pos + len(title)

            updated = (
                original[:insert_pos]
                + "\n\n"
                + section
                + original[insert_pos:]
            )

        else:
            updated = (
                original.rstrip()
                + ("\n\n" if original.strip() else "")
                + title
                + "\n\n"
                + section
                + "\n"
            )

    README_PATH.write_text(updated, encoding="utf-8")


def main():
    """Generate per-module reports and optionally update the README."""
    args = parse_args()
    results = load_results()
    REPORTS_DIRECTORY.mkdir(parents=True, exist_ok=True)
    assets = REPORTS_DIRECTORY / "assets"
    assets.mkdir(parents=True, exist_ok=True)

    for module in results["modules"]:
        report = build_module_report(
            module, results["generated_at"], results.get("complete", False)
        )
        destination = REPORTS_DIRECTORY / f"{module['module']}.md"
        destination.write_text(report, encoding="utf-8")
        (assets / f"{module['module']}.svg").write_text(
            render_svg(
                f"{module['module']} / TEST REPORT",
                summarize(module_tests(module)),
                results["generated_at"],
                [(scope["scope"], summarize(scope["tests"])) for scope in module["scopes"]],
                results.get("complete", False),
            ),
            encoding="utf-8",
        )
        print(f"Generated {destination.relative_to(ROOT)}")

    if not args.skip_readme:
        (assets / "dashboard.svg").write_text(
            render_svg(
                "STRATEGYENGINE / TEST HEALTH",
                summarize([test for module in results["modules"] for test in module_tests(module)]),
                results["generated_at"],
                [(module["module"], summarize(module_tests(module))) for module in results["modules"]],
                results.get("complete", False),
            ),
            encoding="utf-8",
        )
        update_readme(build_dashboard(results))
        print("Updated README.md testing dashboard")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
