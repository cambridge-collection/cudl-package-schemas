from pathlib import Path
import json

import pytest
import jsonschema
import json5

from schema_testing import BaseDatatypeTest


class CUDLSchemaTest(BaseDatatypeTest):
    schema_base_uri = 'https://schemas.cudl.lib.cam.ac.uk/package/v1/'


class TestCollection(CUDLSchemaTest):
    data_type = 'collection'
    expected_valid_count = 2
    expected_invalid_count = 2


class TestItem(CUDLSchemaTest):
    data_type = 'item'
    expected_valid_count = 2
    expected_invalid_count = 1


class TestCUDLItem(CUDLSchemaTest):
    data_type = 'cudl-item'
    expected_valid_count = 0
    expected_invalid_count = 0


class TestMUDLItem(CUDLSchemaTest):
    data_type = 'mudl-item'
    expected_valid_count = 1
    expected_invalid_count = 0


@pytest.fixture(scope='module')
def draft07_strict_meta_schema():
    with open(Path(__file__).parents[2] / 'support' / 'draft-07-strict-schema.json5') as f:
        return json5.load(f)


@pytest.mark.parametrize(
    'schema_path',
    [str(p) for p in Path(__file__).parents[1].glob('schemas/*.json')],
    ids=lambda p: Path(p).name)
def test_schemas_match_strict_meta_schema(schema_path,
                                          draft07_strict_meta_schema):
    with open(schema_path) as f:
        schema = json.load(f)

    jsonschema.validate(schema, draft07_strict_meta_schema)
