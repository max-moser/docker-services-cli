# SPDX-FileCopyrightText: 2020 CERN.
# SPDX-FileCopyrightText: 2024 Graz University of Technology.
# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o.
# SPDX-FileCopyrightText: 2026 TU Wien.
# SPDX-License-Identifier: MIT

"""Environment module."""

import logging
import os
import re
import sys

import click

from .config import SERVICE_TYPES, SERVICES, SERVICES_ALL_DEFAULT_VERSIONS


def normalize_service_name(service_with_version):
    """Return the name of the passed service without version number."""
    service_name = None
    if service_with_version in SERVICES:
        service_name = service_with_version
    else:
        for name in SERVICES:
            if name in service_with_version:
                service_name = name
                break

    return service_name


def _set_default_env(services_version, default_version):
    """Set environmental variable value if it does not exist."""
    os.environ[services_version] = os.environ.get(services_version, default_version)


def _is_version(version):
    """Checks if a string is a version of the format `x.y.z`.

    NOTE: It is not mandatory to be up to patch level. The following would be
    accepted:
    - 10.1
    - 9
    - 15.0.1a2
    """
    try:
        # the regex is taken from distutil's StrictVersion
        version_re = re.compile(
            r"^(\d+) (\. (\d+) (\. (\d+))? ([ab](\d+))?)?$", re.VERBOSE | re.ASCII
        )
        return version_re.match(version)
    except Exception:
        return False


def _load_or_set_env(services_version, default_version):
    """Set a specific service version from the environment.

    It parses the value to distinguish between a version and a defined latest.
    NOTE: It requires that all variables for latest versions have been set up.
    """
    version_from_env = os.environ.get(services_version, default_version)
    # e.g. the ES_7_LATEST string from env, need a second get.
    major_version_from_env = os.environ.get(version_from_env)

    if not version_from_env:
        os.environ[services_version] = default_version

    elif (
        _is_version(version_from_env)
        # for example for minio, where we do not have a semantic version
        or version_from_env == "latest"
    ):
        os.environ[services_version] = version_from_env

    elif major_version_from_env and (
        _is_version(major_version_from_env)
        # for example for minio, where we do not have a semantic version
        or major_version_from_env == "latest"
    ):
        os.environ[services_version] = major_version_from_env

    else:
        click.secho(
            f"Environment variable for version {version_from_env} not set \
            or set to a non-compliant format (dot separated numbers).",
            fg="red",
        )
        sys.exit(1)


def override_default_versions_in_env(requested_services=None):
    """Override default version entries for services in the environment.

    For each service in the list of ``requested_services`` that have a specific major
    version attached to their name as suffix (e.g. ``postgresql11`` instead of
    ``postgresql``), override the environment variable specifying the service's
    version to be used (based on the suffix).
    If the requested version is unavailable, execution will be aborted with a
    suggestion about available values.

    :param requested_services: List of service names, optionally with a major version
        as a suffix; e.g. ``postgresql11``.
    """
    # we're only interested in non-standard service specifications
    # e.g. we look into "postgresql11" but not "postgresql"
    customized_services = set(requested_services or []).difference(SERVICES.keys())

    for customization in customized_services:
        service_name = normalize_service_name(customization)
        if not service_name:
            click.secho(f"Could not identify the service {service_name}", fg="red")
            exit(1)

        major_version = customization.replace(service_name, "")
        default_version = SERVICES_ALL_DEFAULT_VERSIONS.get(
            f"{service_name.upper()}_{major_version}_LATEST"
        )
        if default_version:
            os.environ[f"{service_name.upper()}_VERSION"] = default_version

        else:
            # if we could not find a fitting entry for the requested service + version,
            # we make suggestions based on the available version values
            available_major_versions = [
                v.split(".")[0]
                for v in SERVICES[service_name]["DEFAULT_VERSIONS"].values()
            ]
            click.secho(
                f"No major version {major_version} for {service_name}. "
                f"Please use one of the available ones: {available_major_versions}",
                fg="red",
            )
            exit(1)


def set_env():
    """Export the environment variables for services and versions."""
    for key, value in SERVICES_ALL_DEFAULT_VERSIONS.items():
        _set_default_env(key, value)

    for service in SERVICES.values():
        for key, value in service.items():
            if key.endswith("_VERSION"):
                _load_or_set_env(key, value)
            elif key == "CONTAINER_CONFIG_ENVIRONMENT_VARIABLES":
                for envvar_name, envvar_value in value.items():
                    _set_default_env(envvar_name, envvar_value)


def print_setup_env_config(services, called_from, env_set_command="export"):
    """Prints setup environment instructions."""
    should_print_instructions = False
    for service_type, services_list in services.items():
        if called_from == "up" and len(services_list) > 1:
            logging.warning(
                f"Multiple {service_type} services {services_list} are being configured. "
                f"Note that only {services_list[-1]} will be accessible.",
            )

        for key, value in get_service_env_vars(service_type, services_list):
            command = f"{env_set_command} {key}"
            if env_set_command == "export":
                command += f"={value}"
            click.echo(command)
            should_print_instructions = True

    if should_print_instructions:
        click.secho("# Configure your environment running:", fg="yellow")
        instructions = f'# eval "$(docker-services-cli {called_from}'
        if called_from == "up" and services != SERVICE_TYPES:
            instructions += " " + " ".join(
                [
                    f"--{service_type} {service}"
                    for service_type, services_list in services.items()
                    for service in services_list
                ]
            )
        instructions += ' --env)"'
        click.secho(instructions, fg="yellow")


def get_service_env_vars(service_type, services_list):
    """Get all or a subset of service environment variables."""
    envvars = []
    for service in services_list:
        service_envvars_by_type = (
            SERVICES.get(normalize_service_name(service))
            .get("CONTAINER_CONNECTION_ENVIRONMENT_VARIABLES", {})
            .get(service_type, {})
            .items()
        )
        for key, value in service_envvars_by_type:
            envvars.append((key, value))

    return envvars
