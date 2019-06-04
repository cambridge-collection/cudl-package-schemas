from pathlib import Path
import json

import pytest
import jsonschema
import json5

from schema_testing import BaseDatatypeTest, describe_validation_error


class TestInternalItem(BaseDatatypeTest):
    schema_base_uri = 'https://schemas.cudl.lib.cam.ac.uk/__internal__/v1/'
    data_type = 'item'
    expected_valid_count = 4
    expected_invalid_count = 11


@pytest.fixture(scope='module')
def draft07_strict_meta_schema():
    with open(Path(__file__).parents[2] /
              'support' / 'draft-07-strict-schema.json5') as f:
        return json5.load(f)


@pytest.mark.parametrize(
    'schema_path', Path(__file__).parents[1].glob('schemas/*.json'),
    ids=lambda p: Path(p).name)
def test_schemas_match_strict_meta_schema(schema_path,
                                          draft07_strict_meta_schema):
    with open(schema_path) as f:
        schema = json.load(f)

    with describe_validation_error(instance_name=schema_path.name,
                                   schema_name='strict draft 07 meta schema'):
        jsonschema.validate(schema, draft07_strict_meta_schema)
