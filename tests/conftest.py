import pytest

from django.test import Client

from tests.factories import AdminUserFactory, UserFactory


@pytest.fixture
def user_client(db):
    """Create logged in user."""
    user = UserFactory()
    user.set_password('user')
    user.save()

    client = Client()
    client.login(username=user.username, password='user')
    return client


@pytest.fixture
def admin_client(db):
    """Create logged in admin user."""
    admin = AdminUserFactory()
    admin.set_password('admin')
    admin.save()

    client = Client()
    client.login(username=admin.username, password='admin')
    return client


@pytest.fixture
def client_mapping(client, user_client, admin_client, **kwargs):
    """Contain all client types in single fixture."""
    mapping = {
        'anonymous': client,
        'user': user_client,
        'admin': admin_client,
    }
    for k, v in kwargs.items():
        mapping[k] = v
    return mapping
