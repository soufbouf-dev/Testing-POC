# example · Test Report

[← Testing dashboard](../README.md#testing-dashboard)

![example test summary](assets/example.svg)


---

## ❌ Calculator

**6/7 passed** · 85.7%

| Test | Priority | Result | Time |
|:---|:---:|:---:|---:|
| `add` | Critical | ❌ Failed | 0.0182 ms |
| `divide` | Critical | ✅ Passed | 0.0056 ms |
| `divide_by_zero` | Critical | ✅ Passed | 0.0037 ms |
| `divide_negative` | Critical | ✅ Passed | 0.0031 ms |
| `multiply` | Critical | ✅ Passed | 0.0021 ms |
| `multiply_negative` | Critical | ✅ Passed | 0.0021 ms |
| `subtract` | Critical | ✅ Passed | 0.0022 ms |

### Failure diagnostics

<details>
<summary><strong>❌ Failed · add</strong></summary>

```text
Expected: 3.15
Actual:   3.1
```

</details>


---

## ⚠️ Misc

**2/4 passed** · 50.0%

| Test | Priority | Result | Time |
|:---|:---:|:---:|---:|
| `format_result` | Standard | ✅ Passed | 0.0064 ms |
| `format_round_up` | Standard | ❌ Failed | 0.0039 ms |
| `operation_label` | Standard | 💥 Error | 1.1709 ms |
| `operation_label_error` | Standard | ✅ Passed | 0.0077 ms |

### Failure diagnostics

<details>
<summary><strong>❌ Failed · format_round_up</strong></summary>

```text
Expected: '2.15'
Actual:   '2.16'
```

</details>

<details>
<summary><strong>💥 Error · operation_label</strong></summary>

```text
Traceback (most recent call last):
  File "C:\Users\s.boufrahi\Documents\Qlib\testing_poc\testing\runner.py", line 139, in run_test
    result = test_function()
  File "C:\Users\s.boufrahi\Documents\Qlib\testing_poc\example\tests\test_misc.py", line 28, in test_operation_label
    actual = operation_label(operation)
  File "C:\Users\s.boufrahi\Documents\Qlib\testing_poc\example\calculator.py", line 51, in operation_label
    raise ValueError(f"Unknown operation: {operation}")
ValueError: Unknown operation: addy
```

</details>


---

<sub>Generated from <code>reports/results.json</code>.</sub>
