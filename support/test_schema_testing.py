import pytest

import schema_testing


@pytest.mark.parametrize('src, dest, url, expected', [
    ('https://schemas.cudl.lib.cam.ac.uk/package/v1/',
     'file:///foo/bar/',
     'https://schemas.cudl.lib.cam.ac.uk/package/v1/',
     (True, 'file:///foo/bar/')),

    # Trailing slash on remapped path follows input path
    ('https://schemas.cudl.lib.cam.ac.uk/package/v1/',
     'file:///foo/bar/',
     'https://schemas.cudl.lib.cam.ac.uk/package/v1',
     (True, 'file:///foo/bar')),
    ('https://schemas.cudl.lib.cam.ac.uk/package/v1/',
     'file:///foo/bar/',
     'https://schemas.cudl.lib.cam.ac.uk/package/v1/foo/',
     (True, 'file:///foo/bar/foo/')),
    ('https://schemas.cudl.lib.cam.ac.uk/package/v1/',
     'file:///foo/bar/',
     'https://schemas.cudl.lib.cam.ac.uk/package/v1/foo',
     (True, 'file:///foo/bar/foo')),

    # input fragment and query are preserved
    ('https://schemas.cudl.lib.cam.ac.uk/package/v1/',
     'file:///foo/bar/',
     'https://schemas.cudl.lib.cam.ac.uk/package/v1/foo?a=1#abc',
     (True, 'file:///foo/bar/foo?a=1#abc')),

    # input URL's path doesn't match src - not remapped
    ('https://schemas.cudl.lib.cam.ac.uk/package/v1/',
     'file:///foo/bar/',
     'https://schemas.cudl.lib.cam.ac.uk/package/v2/',
     (False, 'https://schemas.cudl.lib.cam.ac.uk/package/v2/')),

    # input URL's scheme doesn't match src - not remapped
    ('https://schemas.cudl.lib.cam.ac.uk/package/v1/',
     'file:///foo/bar/',
     'foo://schemas.cudl.lib.cam.ac.uk/package/v1/',
     (False, 'foo://schemas.cudl.lib.cam.ac.uk/package/v1/')),

    # input URL's netloc doesn't match src - not remapped
    ('https://schemas.cudl.lib.cam.ac.uk/package/v1/',
     'file:///foo/bar/',
     'https://foo.cudl.lib.cam.ac.uk/package/v1/',
     (False, 'https://foo.cudl.lib.cam.ac.uk/package/v1/')),
])
def test_uri_remapper(src, dest, url, expected):
    remap = schema_testing.url_remapper(src, dest)
    assert remap(url) == expected
