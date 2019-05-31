# Internal JSON format.

This is form use within the CUDL digital library platform and is defined here so that and conversions can be validated.

This format should not be used directly and may be changed without notice.  Use the [JSON-package-format](../JSON-package-format) instead.

## Testing

As with the other schemas, there are tests for the internal item schema in the
[tests](./tests) directory.

In addition, [tests/integration](./tests/integration) contains a shell script which can validate the internal item schema against all the CUDL JSON data. This integration test isn't run when the normal tests are executed.
