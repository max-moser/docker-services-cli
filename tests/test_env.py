# SPDX-FileCopyrightText: 2020 CERN.
# SPDX-License-Identifier: MIT

"""Module tests."""

import os

import pytest

from docker_services_cli.config import SERVICES
from docker_services_cli.env import (
    _is_version,
    _load_or_set_env,
    override_default_versions_in_env,
    set_env,
)


def test_is_version():
    assert _is_version("10")
    assert _is_version("10.1")
    assert _is_version("10.1.2")
    assert _is_version("10.1.2a3")
    assert not _is_version("SERVICE_10_LATEST")


def test_load_or_set_env_default():
    """Tests the loading of a given default value."""
    _load_or_set_env("TEST_VERSION_DEFAULT", "1.0.0")

    assert os.environ.get("TEST_VERSION_DEFAULT") == "1.0.0"

    del os.environ["TEST_VERSION_DEFAULT"]


def test_load_or_set_env_from_value():
    """Tests the loading of a set value."""
    os.environ["TEST_VERSION_DEFAULT"] = "2.0.0"
    _load_or_set_env("TEST_VERSION_DEFAULT", "1.0.0")

    assert os.environ.get("TEST_VERSION_DEFAULT") == "2.0.0"

    del os.environ["TEST_VERSION_DEFAULT"]


def test_load_or_set_env_from_string():
    """Tests the loading of a service default value from string."""
    os.environ["TEST_SERVICE_VERSION_DEFAULT"] = "1.0.0"
    os.environ["TEST_VERSION_DEFAULT"] = "TEST_SERVICE_VERSION_DEFAULT"
    _load_or_set_env("TEST_VERSION_DEFAULT", "2.0.0")

    assert os.environ.get("TEST_VERSION_DEFAULT") == "1.0.0"

    del os.environ["TEST_SERVICE_VERSION_DEFAULT"]
    del os.environ["TEST_VERSION_DEFAULT"]


def test_setversion_not_set():
    """Tests the loading when it results in a system exit."""
    os.environ["TEST_VERSION_DEFAULT"] = "TEST_NOT_EXISTING"

    with pytest.raises(SystemExit) as ex:
        _load_or_set_env("TEST_VERSION_DEFAULT", "2.0.0")

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
    set_env()  # set default environment
    override_default_versions_in_env([service_and_version_string])
    assert os.getenv(envvar) == expected_value
