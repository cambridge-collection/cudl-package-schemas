import sys
from pathlib import Path

sys.path.append(Path(__file__).parent / 'support')

# We need to register the schema_testing plugin before test_schemas imports it,
# otherwise pytest can't perform its module rewriting.
pytest_plugins = ('schema_testing',)
