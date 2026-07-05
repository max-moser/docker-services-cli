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


def _is_version(version, allow_latest=False):
    """Checks if a string is a version of the format `x.y.z`.

    If ``allow_latest`` is set, then "latest" is also accepted.

    NOTE: It is not mandatory to be up to patch level. The following would be accepted:
    - 10.1
    - 9
    - 15.0.1a2
    """
    try:
        if version == "latest" and allow_latest:
            return True

        # the regex is taken from distutil's StrictVersion
        version_re = re.compile(
            r"^(\d+) (\. (\d+) (\. (\d+))? ([ab](\d+))?)?$", re.VERBOSE | re.ASCII
        )
        return version_re.match(version)
    except Exception:
        return False


def _set_service_version_in_env(service_version_key, default_if_unset):
    """Determine the version for the service to use, and set the appropriate env var.

    First, the environment is checked for version specifications.
    If no value is specified, the ``default_if_unset`` is used.

    If the determined value is neither a version number nor "latest", it will be
    interpreted as the name for another environment variable to look up and use as
    version number (this is generally used by the default config).

    If a valid version can be determined, it will be set in the environment.
    Otherwise, execution will be aborted.
    """
    version = os.environ.get(service_version_key, default_if_unset)
    if version and not _is_version(version, allow_latest=True):
        # next to "normal" version numbers, we also support references to other config
        # values via their name (e.g. ``POSTGRESQL_VERSION="POSTGRESQL_16_LATEST"``)
        version = os.environ.get(version, None)

    if version and _is_version(version, allow_latest=True):
        os.environ[service_version_key] = version
    else:
        click.secho(
            f"{service_version_key} has an invalid version format: {version}",
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


def populate_env_configuration():
    """Export the environment variables for default services and versions."""
    for version_key, version_value in SERVICES_ALL_DEFAULT_VERSIONS.items():
        os.environ.setdefault(version_key, version_value)

    for service_config in SERVICES.values():
        for config_key, config_value in service_config.items():
            if config_key.endswith("_VERSION"):
                _set_service_version_in_env(config_key, config_value)

            elif config_key in ["CONTAINER_CONFIG_ENVIRONMENT_VARIABLES", "PORTS"]:
                for envvar_name, envvar_value in config_value.items():
                    os.environ.setdefault(envvar_name, str(envvar_value))


def print_setup_env_config(
    services, called_from, env_set_command="export", env_prefix=""
):
    """Prints setup environment instructions."""
    should_print_instructions = False
    for service_type, services_list in services.items():
        if called_from == "up" and len(services_list) > 1:
            logging.warning(
                f"Multiple {service_type} services {services_list} are being configured. "
                f"Note that only {services_list[-1]} will be accessible.",
            )

        for key, value in get_service_env_vars(service_type, services_list):
            command = f"{env_set_command} {env_prefix}{key}"
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
        service_name = normalize_service_name(service)
        service_config = SERVICES.get(service_name)

        service_envvars_by_type = (
            service_config.get("CONTAINER_CONNECTION_ENVIRONMENT_VARIABLES", {})
            .get(service_type, {})
            .items()
        )

        for env_name, env_value in service_envvars_by_type:
            # replace the port placeholders in the env vars (i.e. connection strings)
            for port_var_name, default_port in service_config.get("PORTS", {}).items():
                port = os.environ.get(port_var_name, default_port)
                env_value = env_value.replace(f"{{{port_var_name}}}", str(port))

            envvars.append((env_name, env_value))

    return envvars


def randomize_service_ports_env(services_list):
    """Set each service's ports to special value 0 in the environment.

    On Unix systems, binding to port 0 has the special meaning of assigning a random
    free port.
    """
    for service in services_list:
        service_name = normalize_service_name(service)
        service_config = SERVICES.get(service_name)
        for port_var_name, default_port in service_config.get("PORTS", {}).items():
            os.environ[port_var_name] = "0"
