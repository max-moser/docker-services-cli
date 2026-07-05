# SPDX-FileCopyrightText: 2020 CERN.
# SPDX-License-Identifier: MIT

"""Module tests."""

import os
import random

import pytest

from docker_services_cli.config import SERVICES, ServiceType
from docker_services_cli.env import (
    _is_version,
    _set_service_version_in_env,
    get_service_env_vars,
    override_default_versions_in_env,
    populate_env_configuration,
)


def test_is_version():
    assert _is_version("10")
    assert _is_version("10.1")
    assert _is_version("10.1.2")
    assert _is_version("10.1.2a3")
    assert _is_version("latest", allow_latest=True)
    assert not _is_version("latest")
    assert not _is_version("SERVICE_10_LATEST")


def test_load_or_set_env_default():
    """Tests the loading of a given default value."""
    _set_service_version_in_env("TEST_VERSION_DEFAULT", "1.0.0")

    assert os.environ.get("TEST_VERSION_DEFAULT") == "1.0.0"

    del os.environ["TEST_VERSION_DEFAULT"]


def test_load_or_set_env_from_value():
    """Tests the loading of a set value."""
    os.environ["TEST_VERSION_DEFAULT"] = "2.0.0"
    _set_service_version_in_env("TEST_VERSION_DEFAULT", "1.0.0")

    assert os.environ.get("TEST_VERSION_DEFAULT") == "2.0.0"

    del os.environ["TEST_VERSION_DEFAULT"]


def test_load_or_set_env_from_string():
    """Tests the loading of a service default value from string."""
    os.environ["TEST_SERVICE_VERSION_DEFAULT"] = "1.0.0"
    os.environ["TEST_VERSION_DEFAULT"] = "TEST_SERVICE_VERSION_DEFAULT"
    _set_service_version_in_env("TEST_VERSION_DEFAULT", "2.0.0")

    assert os.environ.get("TEST_VERSION_DEFAULT") == "1.0.0"

    del os.environ["TEST_SERVICE_VERSION_DEFAULT"]
    del os.environ["TEST_VERSION_DEFAULT"]


def test_setversion_not_set():
    """Tests the loading when it results in a system exit."""
    os.environ["TEST_VERSION_DEFAULT"] = "TEST_NOT_EXISTING"

    with pytest.raises(SystemExit) as ex:
        _set_service_version_in_env("TEST_VERSION_DEFAULT", "2.0.0")

    assert ex.value.code == 1

    del os.environ["TEST_VERSION_DEFAULT"]


@pytest.mark.parametrize(
    "service_and_version_string,envvar,expected_value",
    [
        # case in which no version is passed, default value should be used
        (
            "elasticsearch",
            "ELASTICSEARCH_VERSION",
            SERVICES["elasticsearch"]["DEFAULT_VERSIONS"][
                SERVICES["elasticsearch"]["ELASTICSEARCH_VERSION"]
            ],
        ),
        # case in which a wrong version is passed, fails
        pytest.param(
            "postgresql-1",
            "POSTGRESQL_VERSION",
            SERVICES["postgresql"]["DEFAULT_VERSIONS"][
                SERVICES["postgresql"]["POSTGRESQL_VERSION"]
            ],
            marks=pytest.mark.xfail,
        ),
        # case in which a correct non default version is passed
        (
            "mysql8",
            "MYSQL_VERSION",
            SERVICES["mysql"]["DEFAULT_VERSIONS"]["MYSQL_8_LATEST"],
        ),
    ],
)
def test_override_default_service_versions(
    service_and_version_string, envvar, expected_value
):
    """Test overriding default versions with service+version strings."""
    populate_env_configuration()  # set default environment
    override_default_versions_in_env([service_and_version_string])
    assert os.getenv(envvar) == expected_value


def test_service_port_overrides_default():
    """Test the default port assignment for a service."""
    # make sure that the environment is clean enough to start
    os.environ.pop("ELASTICSEARCH_PORT", None)
    assert "ELASTICSEARCH_PORT" not in os.environ

    # check if the default value for the port gets pushed into the environment
    populate_env_configuration()
    assert os.getenv("ELASTICSEARCH_PORT") == "9200"

    # check if the default port gets inserted correctly into the connection string
    vars = get_service_env_vars(ServiceType.search.value, ["elasticsearch"])
    assert len(vars) == 1
    assert ("SEARCH_HOSTS", "\"[{'host': 'localhost', 'port': 9200}]\"") in vars


def test_service_port_overrides_random():
    """Test assignment of a random port for a service.

    NOTE that port 0 is a special case (assigns a random free port).
    Since this would require checking the docker daemon for the assigned public ports,
    this cannot be covered here in this test case!
    """
    # set a random value for the port
    port = str(random.randint(10000, 30000))
    os.environ["ELASTICSEARCH_PORT"] = port

    # check if the assigned value for the port gets pushed into the environment
    populate_env_configuration()
    assert os.getenv("ELASTICSEARCH_PORT") == port

    # check if the assigned port gets inserted correctly into the connection string
    vars = get_service_env_vars(ServiceType.search.value, ["elasticsearch"])
    connection_string = vars[0][1]
    assert len(vars) == 1
    assert ("SEARCH_HOSTS", f"\"[{{'host': 'localhost', 'port': {port}}}]\"") in vars
    assert "localhost" in connection_string
    assert "9200" not in connection_string
