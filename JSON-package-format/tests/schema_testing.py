"""
A simple pytest plugin to test schemas against valid and invalid test data.

When this plugin is activated, subclasses of BaseDatatypeTest define tests for
a JSON schema.
"""
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List
from urllib.parse import quote, unquote

import json5
import jsonpatch
import pytest
from jsonschema import Draft7Validator, RefResolver, ValidationError
from rfc3987 import parse, resolve, compose

JPF_DIR = (Path(__file__) / '../..').resolve()
SCHEMA_DIR = JPF_DIR / 'schemas'
TEST_DIR = JPF_DIR / 'tests'


def uri_to_path(uri):
    parts = parse(uri, 'URI')
    if parts['scheme'] != 'file':
        raise ValueError(f'uri is not a file:// URL: {uri}')
    return Path(unquote(parts['path']))


def path_to_uri(path: Path):
    if isinstance(path, str):
        path = Path(path)
    uri = path.as_uri()
    if path.is_dir():
        # paths which are DIRs should end with a slash so that we can resolve
        # off them without losing the dir.
        return uri + '/'
    return uri


def validate_path_under_dir(dir):
    def path_under_dir_validator(path):
        if dir not in path.parents:
            raise ValueError(f'{path} is not a sub-path of {dir}')
    return path_under_dir_validator


def url_remapper(src, dest):
    src_parts = parse(src, 'URI')
    dest_parts = parse(dest, 'URI')

    src_path = Path(unquote(src_parts['path'])).resolve()
    dest_path = Path(unquote(dest_parts['path'])).resolve()

    def remap(url):
        url_parts = parse(url, 'URI')
        if not (url_parts['scheme'] == src_parts['scheme'] and
                url_parts['authority'] == src_parts['authority']):
            return False, url

        url_path = Path(unquote(url_parts['path'])).resolve()
        if src_path != url_path and src_path not in url_path.parents:
            return False, url

        result_path = dest_path / url_path.relative_to(src_path)

        # Use a trailing slash if the incoming path had one. This facilitates
        # further URI resolution operations.
        if url_parts['path'].endswith('/'):
            final_path = f'{result_path}/'
        else:
            final_path = str(result_path)

        return True, (compose(
            scheme=dest_parts['scheme'], authority=dest_parts['authority'],
            path=quote(final_path), query=url_parts['query'],
            fragment=url_parts['fragment']))
    return remap


def handle_file_uri_request(uri, validate_path=None):
    path = uri_to_path(uri)

    if validate_path is not None:
        validate_path(path)

    with open(path, 'r') as f:
        return json.load(f)


def cudl_schema_url_handler():
    """Handle requests for CUDL schema URLs by providing local schema files
    """
    remap = url_remapper(
        'https://schemas.cudl.lib.cam.ac.uk/package/v1/',
        path_to_uri(SCHEMA_DIR))
    validator = validate_path_under_dir(SCHEMA_DIR)

    def handle(uri):
        remapped, uri = remap(uri)

        if not remapped:
            raise ValueError(f'Unable to handle URI: {uri}')

        return handle_file_uri_request(uri, validate_path=validator)
    return handle


def get_test_data_path(type_name):
    return TEST_DIR / type_name


def list_testcases(type_name, testcase_type, expected_count=None):
    dir = get_test_data_path(type_name)
    result = (set(dir.glob(f'{testcase_type}/*.json')) |
              set(dir.glob(f'{testcase_type}/*.json5')))

    if expected_count is not None and len(result) != expected_count:
        msg = f'expected {expected_count} testcases but found 0'
        assert len(result) >= expected_count, msg
        import warnings
        warnings.warn(msg)
    return result


@dataclass
class PatchedJsonValue:
    base_value: dict
    patch: list

    @property
    def value(self):
        return jsonpatch.apply_patch(self.base_value, self.patch)

    @classmethod
    def from_testcase(cls, test_case_path, base_path_validator=None):
        with open(test_case_path) as f:
            test_case = json5.load(f)
        tc_path_url = path_to_uri(test_case_path)
        base_value_path = uri_to_path(resolve(tc_path_url, test_case['base']))

        if base_path_validator is not None:
            base_path_validator(base_value_path)

        with open(base_value_path) as f:
            base_value = json5.load(f)

        return PatchedJsonValue(base_value=base_value,
                                patch=test_case['patch'])


@dataclass
class InvalidInstanceTestCase:
    data: PatchedJsonValue
    validation_error_validator: Callable[[List[ValidationError]], None]


def create_messages_validator(expected_error):
    if isinstance(expected_error, str):
        expected_error = {'contains': expected_error}

    [(method, value)] = expected_error.items()
    if method == 'exact':
        pattern = re.compile(f'^{re.escape(value)}$')
    elif method == 'contains':
        pattern = re.compile(re.escape(value))
    elif method == 'regex':
        pattern = re.compile(value)
    else:
        raise ValueError(
            f'Unsupported expectedError value: {expected_error!r}')

    def validate(error_messages):
        assert any(pattern.search(msg) for msg in error_messages), (
            f'Expected search for {pattern} to match at least one of '
            f'{error_messages}')
    return validate


def create_validation_error_validator(expected_errors):
    if isinstance(expected_errors, str):
        expected_errors = [expected_errors]

    validators = [create_messages_validator(e) for e in expected_errors]

    def validate_validation_errors(errors):
        assert len(errors) > 0, (
            'instance unexpectedly passed schema validation')

        messages = [e.message for e in errors]
        for validator in validators:
            validator(messages)
    return validate_validation_errors


@pytest.fixture(scope='class')
def valid_instance(valid_instance_path):
    with open(valid_instance_path) as f:
        return json5.load(f)


@pytest.fixture(scope='class')
def invalid_instance_testcase(data_type, invalid_testcase_path):
    with open(invalid_testcase_path) as f:
        test_case = json5.load(f)
    tc_path_url = path_to_uri(invalid_testcase_path)
    base_value_path = uri_to_path(resolve(tc_path_url, test_case['base']))

    validate_path_under_dir(get_test_data_path(data_type))(base_value_path)

    with open(base_value_path) as f:
        base_value = json5.load(f)

    patched_value = PatchedJsonValue(
        base_value=base_value, patch=test_case['patch'])

    err_validator = create_validation_error_validator(
        test_case.get('expectedErrors') or ())

    return InvalidInstanceTestCase(
        data=patched_value, validation_error_validator=err_validator)


@pytest.fixture(scope='session')
def ref_resolver():
    handlers = {
        'https': cudl_schema_url_handler()
    }
    return RefResolver(base_uri=path_to_uri(SCHEMA_DIR),
                       referrer=None, handlers=handlers)


@pytest.fixture(scope='class')
def schema(ref_resolver, schema_id):
    id, schema = ref_resolver.resolve(schema_id)
    Draft7Validator.check_schema(schema)
    return Draft7Validator(schema, resolver=ref_resolver)


def pytest_generate_tests(metafunc):
    if metafunc.cls and issubclass(metafunc.cls, BaseDatatypeTest):
        metafunc.cls.generate_parameters(metafunc)


class BaseDatatypeTest:
    """
    When subclassed, this tests a schema against a set of valid and invalid
    test cases, defined as JSON files.

    Subclasses must define class properties for:

    - ``data_type`` — The name of the schema being tested

    And optionally for:

    - ``expected_valid_count``
    - ``expected_invalid_count``

    If the number of valid/invalid test cases is less than these values the
    test setup will fail. If it's more then a warning will be triggerd.
    """
    data_type = None
    expected_valid_count = None
    expected_invalid_count = None

    @classmethod
    def generate_parameters(cls, metafunc):
        data_type = metafunc.cls.data_type
        valid_count = metafunc.cls.expected_valid_count
        invalid_count = metafunc.cls.expected_invalid_count

        if data_type is None:
            raise TypeError(f'No data_type specified, {cls} must have a '
                            f'data_type property')

        if 'data_type' in metafunc.fixturenames:
            metafunc.parametrize('data_type', [data_type], scope='class')

        if 'schema_id' in metafunc.fixturenames:
            metafunc.parametrize('schema_id', [f'{data_type}.json'],
                                 scope='class')

        if 'valid_instance_path' in metafunc.fixturenames:
            paths = list_testcases(data_type, 'valid',
                                   expected_count=valid_count)
            metafunc.parametrize('valid_instance_path', paths, scope='class')

        if 'invalid_testcase_path' in metafunc.fixturenames:
            paths = list_testcases(data_type, 'invalid',
                                   expected_count=invalid_count)
            metafunc.parametrize('invalid_testcase_path', paths, scope='class')

    def test_schema_matches_valid_instance(
        self, schema, valid_instance):
        schema.validate(valid_instance)

    def test_schema_rejects_invalid_instance(
        self, schema, invalid_instance_testcase: InvalidInstanceTestCase):

        errors = list(schema.iter_errors(
            invalid_instance_testcase.data.value))

        invalid_instance_testcase.validation_error_validator(errors)
