"""
A simple pytest plugin to test schemas against valid and invalid test data.

When this plugin is activated, subclasses of BaseDatatypeTest define tests for
a JSON schema.
"""
import importlib
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


def schema_url_handler(schema_id_base_url, local_dir):
    """Handle requests for schema ID URLs by providing local schema files
    """
    remap = url_remapper(schema_id_base_url, path_to_uri(local_dir))
    validator = validate_path_under_dir(local_dir)

    def handle(uri):
        remapped, uri = remap(uri)

        if not remapped:
            raise ValueError(f'Unable to handle URI: {uri}')

        return handle_file_uri_request(uri, validate_path=validator)
    return handle


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


@pytest.fixture(scope='module')
def valid_instance(valid_instance_path):
    with open(valid_instance_path) as f:
        return json5.load(f)


@pytest.fixture(scope='module')
def invalid_instance_testcase(invalid_testcase_path, test_data_dir):
    with open(invalid_testcase_path) as f:
        test_case = json5.load(f)
    tc_path_url = path_to_uri(invalid_testcase_path)
    base_value_path = uri_to_path(resolve(tc_path_url, test_case['base']))

    validate_path_under_dir(test_data_dir)(base_value_path)

    with open(base_value_path) as f:
        base_value = json5.load(f)

    patched_value = PatchedJsonValue(
        base_value=base_value, patch=test_case['patch'])

    err_validator = create_validation_error_validator(
        test_case.get('expectedErrors') or ())

    return InvalidInstanceTestCase(
        data=patched_value, validation_error_validator=err_validator)


@pytest.fixture(scope='module')
def ref_resolver(schema_base_uri, schema_dir):
    base_scheme = parse(schema_base_uri, 'URI')['scheme']
    handlers = {
        base_scheme: schema_url_handler(schema_base_uri, schema_dir)
    }
    return RefResolver(base_uri=path_to_uri(schema_dir),
                       referrer=None, handlers=handlers)


@pytest.fixture(scope='module',
                ids=lambda s: s.get('$id', '<schema-without-id>'))
def schema(ref_resolver, schema_id):
    id, schema = ref_resolver.resolve(schema_id)
    Draft7Validator.check_schema(schema)
    return Draft7Validator(schema, resolver=ref_resolver)


def pytest_generate_tests(metafunc):
    if metafunc.cls and issubclass(metafunc.cls, BaseDatatypeTest):
        metafunc.cls.generate_parameters(metafunc)


def get_file(cls):
    return importlib.import_module(cls.__module__).__file__


class BaseDatatypeTest:
    """
    When subclassed, this tests a schema against a set of valid and invalid
    test cases, defined as JSON files in the following directory structure::

        schemas
        ├── collection.json
        ├── common.json
        ├── cudl.item.schema.json
        ├── item.schema.json
        └── mudl.item.schema.json
        tests
        ├── collection
        │   ├── invalid
        │   │   ├── additional-root-properties.json5
        │   │   └── missing-type.json5
        │   └── valid
        │       ├── kitchen-sink.json
        │       └── minimal.json
        └── test_schemas.py

    The schema's URI is mapped to the ``schemas`` directory.

    Subclasses must define the class properties:

    - ``data_type`` — The name of the schema being tested
    - ``schema_base_uri`` — The URI to map to the local schema dir. Typically
      this is the URI of the schema being tested without the final path
      component. For example, ``https://schemas.cudl.lib.cam.ac.uk/package/v1/``

    And optionally:

    - ``expected_valid_count``
    - ``expected_invalid_count``
    - ``schema_dir`` — The path to the directory containing the schema files.
      defaults to ``{dir_of_test_module}/../schemas``.

    If the number of valid/invalid test cases is less than these values the
    test setup will fail. If it's more then a warning will be triggered.

    Testcase Data
    =============


    """

    # These must be overridden
    data_type = None
    schema_base_uri = None

    # These have defaults if not specified
    expected_valid_count = None
    expected_invalid_count = None
    schema_dir = None

    @classmethod
    def get_schema_base_uri(cls):
        if cls.schema_base_uri is None:
            raise TypeError(f'No schema_base_uri specified, {cls} must have a '
                            f'schema_base_uri property')
        return cls.schema_base_uri

    @classmethod
    def get_schema_dir(cls):
        if cls.schema_dir:
            return cls.schema_dir

        return (Path(get_file(cls)).parent / '../schemas').resolve()

    @classmethod
    def get_data_type(cls):
        if cls.data_type is None:
            raise TypeError(f'No data_type specified, {cls} must have a '
                            f'data_type property')
        return cls.data_type

    @classmethod
    def get_schema_id(cls):
        return f'{cls.get_data_type()}.json'

    @classmethod
    def get_test_data_dir(cls):
        return Path(get_file(cls)).parent / cls.get_data_type()

    @classmethod
    def list_testcases(cls, testcase_type):
        dir = cls.get_test_data_dir()
        return (set(dir.glob(f'{testcase_type}/*.json')) |
                set(dir.glob(f'{testcase_type}/*.json5')))

    @classmethod
    def validate_testcase_paths(cls, testcase_type, expected_count, paths):
        if expected_count is not None and len(paths) != expected_count:
            msg = (
f'expected {cls.get_data_type()} to have {expected_count} {testcase_type} '
f'testcases but found 0')
            assert len(paths) >= expected_count, msg
            import warnings
            warnings.warn(msg)

    @classmethod
    def generate_parameters(cls, metafunc):
        data_type = cls.get_data_type()
        valid_count = cls.expected_valid_count
        invalid_count = cls.expected_invalid_count

        if 'data_type' in metafunc.fixturenames:
            metafunc.parametrize('data_type', [data_type], scope='module')

        if 'schema_id' in metafunc.fixturenames:
            metafunc.parametrize('schema_id', [f'{data_type}.json'],
                                 scope='module')

        if 'schema_base_uri' in metafunc.fixturenames:
            metafunc.parametrize(
                'schema_base_uri', [cls.get_schema_base_uri()], scope='module')

        if 'schema_dir' in metafunc.fixturenames:
            metafunc.parametrize(
                'schema_dir', [cls.get_schema_dir()], scope='module',
                ids=lambda x: str(x))

        if 'test_data_dir' in metafunc.fixturenames:
            metafunc.parametrize(
                'test_data_dir', [cls.get_test_data_dir()], scope='module',
                ids=lambda x: str(x))

        if 'valid_instance_path' in metafunc.fixturenames:
            paths = cls.list_testcases('valid')
            cls.validate_testcase_paths('valid', valid_count, paths)
            metafunc.parametrize('valid_instance_path', paths, scope='module',
                                 ids=lambda x: str(x))

        if 'invalid_testcase_path' in metafunc.fixturenames:
            paths = cls.list_testcases('invalid')
            cls.validate_testcase_paths('invalid', invalid_count, paths)
            metafunc.parametrize(
                'invalid_testcase_path', paths, scope='module',
                ids=lambda x: str(x))

    def test_schema_matches_valid_instance(
        self, schema, valid_instance):
        schema.validate(valid_instance)

    def test_schema_rejects_invalid_instance(
        self, schema, invalid_instance_testcase: InvalidInstanceTestCase):

        errors = list(schema.iter_errors(
            invalid_instance_testcase.data.value))

        invalid_instance_testcase.validation_error_validator(errors)
