# CUDL data packaging schemas

This repository contains schemas for data formats used when building CUDL data
packages.

* [Internal JSON format](./Internal-JSON-format/)
* [JSON Package format](./JSON-package-format/)
* [XML Package format](./XML-package-format/)

## Testing

Automated tests for the schemas are included. They are written in Python with
[pytest]. Dependencies are managed with [poetry]. Tests are run automatically
via Bitbucket Pipelines.

To run the tests locally:

1. [Install poetry][poetry install]
2. Install dependencies: `$ poetry install`
3. Run pytest: `$ poetry run pytest`

[pytest]: https://docs.pytest.org/en/latest/
[poetry]: https://poetry.eustace.io/
[poetry install]: https://poetry.eustace.io/docs/#installation
