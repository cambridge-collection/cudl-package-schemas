from schema_testing import BaseDatatypeTest


pytest_plugins = ('schema_testing',)


class TestCollection(BaseDatatypeTest):
    data_type = 'collection'
    expected_valid_count = 2
    expected_invalid_count = 2
