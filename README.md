## Testing Dashboard

<!-- TESTING_DASHBOARD_START -->

![Repository testing dashboard](reports/assets/dashboard.svg)

🔎 **Dive into the detailed test reports**

[example →](reports/example.md) · [example_2.calc →](reports/example_2.calc.md)

<sub>Generated automatically from the latest test run.</sub>

<!-- TESTING_DASHBOARD_END -->

# How to use?

To use this testing POC in your projects, there are three requirements:

- Add the `testing` folder to your repository. No changes are required to any of the files inside.
- Your test files should follow the `testing/test_file_model.py` and should be put in several folders called `tests`. These folders can be placed anywhere in your repo.
- While you can run the tests manually, there is an optional git hooks setup (in the `/.githooks` folder) that runs tests automatically alongside your commits and pushes. More details can be found below.

Below are a few more explanations on how the tests work:

## Git Hooks Setup

After cloning the repository, activate the shared Git hooks:

```bash
git config core.hooksPath .githooks
chmod +x .githooks/pre-commit .githooks/pre-push
```

This setup only needs to be performed once per clone.

The hooks use the shared testing infrastructure to automate validation and reporting.

- **Pre-commit:** Automatically executes tests, generates reports, and stages the updated reporting files. Test failures do not block commits, although testing infrastructure failures may do so.
- **Pre-push:** Validates proposed pushes to remote `main`. Critical test failures or incomplete validation block the push; standard failures do not. Development branches remain unrestricted by test results.

Hooks are installed locally and are not automatically activated when cloning a repository containing the POC.

## Run Tests Manually

Tests can be executed independently of Git operations.

Run the complete test suite:

```bash
python -m testing.runner
```

Run tests for selected modules:

```bash
python -m testing.runner --modules core backtesting
```

The runner discovers tests recursively within module-specific `tests/` directories.

Tests execute sequentially, and their results are written to:

```text
reports/results.json
```

Each test is classified as either:

- **Critical:** Must pass before pushing to remote `main`.
- **Standard:** Reported without blocking commits or pushes.

Test failures and testing infrastructure failures are distinguished. Incomplete validation is never considered successful.