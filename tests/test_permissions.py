import pytest

from tests.constants import (
    FOUND,
    METHOD_NOT_ALLOWED,
    OK,
)
from tests.utils import (
    assert_permissions,
    get_permissions,
)


ADMIN_VIEW_ACCESS = [
    ('anonymous', FOUND),
    ('user', FOUND),
    ('admin', OK),
]

public_view_permissions = get_permissions(METHOD_NOT_ALLOWED, {'get': 200})
PUBLIC_VIEW_ACCESS = [
    ('anonymous', public_view_permissions),
    ('user', public_view_permissions),
    ('admin', public_view_permissions),
]

PUBLIC_URL_REVERSE = (
    'pgo:breakpoint-calc',
    'pgo:good-to-go',
    'pgo:pokemon-list',
    'pgo:move-list',
)


@pytest.mark.parametrize('client_type, response_code_mapping', ADMIN_VIEW_ACCESS)
def test_admin_view_permissions(client_type, response_code_mapping, client_mapping):
    """Test admin view access permissions."""
    assert_permissions(client_type, response_code_mapping, client_mapping, ('admin:index',))


@pytest.mark.parametrize('client_type, response_code_mapping', PUBLIC_VIEW_ACCESS)
def test_public_view_permissions(client_type, response_code_mapping, client_mapping):
    """Test public view access permissions."""
    assert_permissions(client_type, response_code_mapping, client_mapping, PUBLIC_URL_REVERSE)
