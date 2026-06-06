# TestValidation fixtures

Integration-test configuration fixtures for `NeuroModelerConsole --check-config`.

## Layout

| Directory | Purpose |
|-----------|---------|
| `test_valid/` | Valid project (baseline) |
| `test_missing_model/` | Missing model XML |
| `test_missing_parameters/` | Missing parameters XML |
| `test_invalid_xml/` | Malformed XML |
| `test_empty_model/` | Empty model file |
| `test_invalid_classes/` | Unknown component classes |
| `test_invalid_links/` | Invalid component links |

## See also

- [Tests/Integration/ConfigValidation/README.md](../../../Tests/Integration/ConfigValidation/README.md)
- [Docs/Testing/ConfigValidation-Tests.md](../../../Docs/Testing/ConfigValidation-Tests.md)
