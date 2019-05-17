#!/usr/bin/python3

import json
import jsonschema


# Validates JSON data against the Draft7 schema in item.schema.json
def validate(json_data):
    with open('../../../Internal-JSON-format/schemas/item.schema.json', 'r') as f:
        schema_data = f.read()
    schema = json.loads(schema_data)
    json_obj = json.loads(json_data)

    # If no exception is raised by validate(), the instance is valid.
    jsonschema.Draft7Validator(schema).validate(json_obj)
