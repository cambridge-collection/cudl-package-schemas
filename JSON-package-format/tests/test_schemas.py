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
