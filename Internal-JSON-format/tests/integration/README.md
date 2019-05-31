# Testing the internal schema against all CUDL JSON

This directory contains a standalone script to test the [internal JSON schema](../../schemas/item.json) against all the CUDL item JSON data.

There are a handful of errors in the data which are caught by the schema. By default, the script patches the item schema to allow these minor issues, so that we can validate that the schema as a whole validates the existing data correctly.

## Running

> **Note**: [ajv-cli](https://www.npmjs.com/package/ajv-cli) needs to be installed.

Run [`test-all.sh`](./test-all.sh) with `ITEM_JSON_DIR` set to a directory containing the item JSON files to validate. See the script for a few other envars that can be used to override defaults.

```
$ env ITEM_JSON_DIR=/foo/data/json ./test-all.sh
```

It should exit with no output (other than the message about patching the schema), and with status 0. If data doesn't match, it'll be reported as follows, and exist with non-zero status:

```
$ env ITEM_JSON_DIR=/home/hal/workspace/cudl-data/json ./test-all.sh
Validating with ./../../schemas/item.json patched with ./allow-minor-deviations.patch.json as /tmp/tmp.uKvhqXvfx9 to allow known data errors
/home/hal/workspace/cudl-data/json/MS-DAR-00113.json failed test
[
  {
    keyword: 'pattern',
    dataPath: '/pages/389/thumbnailImageOrientation',
    schemaPath: '#/definitions/orientation/pattern',
    params: {
      pattern: '^(?:(?:portrait|landscape)(?:\\s+(?:portrait|landscape))*)$'
    },
    message: 'should match pattern ' +
      '"^(?:(?:portrait|landscape)(?:\\s+(?:portrait|landscape))*)$"',
    schema: '^(?:(?:portrait|landscape)(?:\\s+(?:portrait|landscape))*)$',
    parentSchema: {
      type: 'string',
      pattern: '^(?:(?:portrait|landscape)(?:\\s+(?:portrait|landscape))*)$'
    },
    data: ''
  }
]
```
