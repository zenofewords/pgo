from copy import copy

from django.conf import settings
from django.urls import reverse


def get_permissions(response_mapping, custom_mapping):
    """
    Build permission mappings.

    :param response_mapping: usually a predefined permission template (FORBIDDEN, NOT_FOUND, etc.)
    :type response_mapping: dict
    :param custom_mapping: key/value pairs which need to be customised
    :type custom_mapping: dict

    :returns: a new response method and status code mapping
    :rtype: dict
    """
    response_mapping = copy(response_mapping)
    response_mapping.update(custom_mapping)
    return response_mapping


def assert_permissions(client_type, response_code_mapping, client_mapping, url_reverse):
    """
    Test URL response depending on client type.

    :param client_type: type of client (anonymous, user, admin, etc.)
    :type client_type: string
    :param response_code_mapping: request type with a matching response code
    :type response_code_mapping: dict
    :param client_mapping: a fixture that contains client types
    :type client_mapping: dict
    :param url_reverse: tuple of reverse strings for URLs which receive requests
    :type url_reverse: tuple
    """
    for method in response_code_mapping.keys():
        for url in url_reverse:
            response_code = getattr(
                client_mapping[client_type], method
            )(reverse(url), secure=not settings.DEBUG).status_code

            assert response_code == response_code_mapping[method], print(
                'client: {}, method: {}, received: {}, expected: {}'.format(
                    client_type, method, response_code, response_code_mapping[method]
                )
            )
