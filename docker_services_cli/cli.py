# SPDX-FileCopyrightText: 2020 CERN.
# SPDX-FileCopyrightText: 2026 TU Wien.
# SPDX-License-Identifier: MIT

"""CLI module."""

import json
import os
from functools import update_wrapper
from pathlib import Path
from subprocess import CalledProcessError

import click

from .config import SERVICE_TYPES, SERVICES
from .env import (
    normalize_service_name,
    override_default_versions_in_env,
    populate_env_configuration,
    print_setup_env_config,
    randomize_service_ports_env,
)
from .services import get_public_service_ports, services_down, services_up


def _get_module_path():
    """Gets the path in which the module is installed."""
    parent_path = Path(__file__).parent
    return str(parent_path)


def env_output(env_set_command):
    """Decorate command to print exportable environment settings."""
    if env_set_command not in ["export", "unset"]:
        click.secho("Wrong environment set command.", fg="red")
        exit(1)

    def print_env_output(func):
        @click.option(
            "--env",
            is_flag=True,
            default=False,
            help="Print export statements to set environment.",
        )
        def _print_env_output(*args, **kwargs):
            env = kwargs.pop("env", False)
            services = kwargs.get("services") or SERVICE_TYPES
            if env:
                # comment command output until env export
                click.echo(": '")

            try:
                click.get_current_context().invoke(func, *args, **kwargs)
            except CalledProcessError as e:
                # in case someting goes wrong (e.g. the ports are already in use)
                # we want to end the comment block after the command output and
                # report an error
                if env:
                    click.echo("'")
                click.echo(f"exit {e.returncode}")
                exit(e.returncode)

            if env:
                # end of multiline comment, start of export statements
                click.echo("'")
                print_setup_env_config(
                    services,
                    click.get_current_context().info_name,
                    env_set_command=env_set_command,
                    env_prefix=kwargs.get("env_prefix", ""),
                )

        return update_wrapper(_print_env_output, func)

    return print_env_output


def services_by_type(func):
    """Decorate command adding all service types as options.

    :param func: The function that implements the Click command to which the
        service types options will be added.

    :return: A wrapped function around the passed Click command which exposes
        all ``config.SERVICES_TYPES`` as Click options. The list of services
        by type is injected as ``services`` keyword argument.
    """

    def collect_services_by_type(*args, **kwargs):
        services = {}
        for service_type in SERVICE_TYPES:
            service = kwargs.pop(service_type)
            if service:
                services.setdefault(service_type, []).extend(
                    service if isinstance(service, list) else [service]
                )

        kwargs["services"] = services
        click.get_current_context().invoke(func, *args, **kwargs)

    def validate_service_name(ctx, service_type, services_list):
        available_services = SERVICE_TYPES.get(service_type.name, [])
        for service in services_list:
            if not (
                normalize_service_name(service)
                or normalize_service_name(service) in available_services
            ):
                raise click.BadParameter(
                    f"{service} is not a valid service of type {service_type.name}. "
                    f"Try one of: \n{available_services}"
                )
        return list(services_list)

    for service_type in SERVICE_TYPES:
        service_types = ", ".join(SERVICE_TYPES.get(service_type))
        click.option(
            f"--{service_type}",
            callback=validate_service_name,
            multiple=True,
            help=(
                f"Specify which service should run as {service_type}. "
                f"Available {service_type} services: {service_types}."
            ),
        )(func)

    return update_wrapper(collect_services_by_type, func)


class ServicesCtx(object):
    """Context class for docker services cli."""

    def __init__(self, filepath, verbose):
        """Constructor."""
        self.filepath = filepath
        self.verbose = verbose


@click.group()
@click.version_option()
@click.option(
    "--filepath",
    "-f",
    required=False,
    default=f"{_get_module_path()}/docker-services.yml",
    type=click.Path(exists=True),
    help="Path to a docker compose file with the desired services definition.",
)
@click.option(
    "--verbose",
    is_flag=True,
    default=False,
    help="Verbose output.",
)
@click.pass_context
def cli(ctx, filepath, verbose):
    """Initialize CLI context."""
    populate_env_configuration()
    ctx.obj = ServicesCtx(filepath=filepath, verbose=verbose)


@cli.command()
@click.option(
    "--wait/--no-wait",
    is_flag=True,
    help="Wait for services to be up (use healthchecks).",
)
@click.option(
    "--retries",
    default=6,
    type=int,
    help="Number of times to retry a service's healthcheck.",
)
@click.option(
    "--randomize-ports",
    is_flag=True,
    default=False,
    help=(
        "Use randomized ports for the services (assign port 0 for each service). "
        "This may not work on all platforms."
    ),
)
@click.option(
    "--env-prefix",
    default="",
    type=str,
    help="Prefix to use for the exported environment variables.",
)
@click.option(
    "--project-name",
    default=None,
    type=str,
    help="Project name to use for the services.",
)
@services_by_type
@env_output(env_set_command="export")
@click.pass_obj
def up(
    services_ctx, services, project_name, wait, retries, randomize_ports, env_prefix
):
    r"""Boots up the required services.

    Example:
        $ docker-services-cli up --db postgresql11

    Note: All services will be boot up if no service is specified.
    """
    _services = [s for services_list in services.values() for s in services_list]

    # NOTE: docker compose boots up all if none is provided
    if len(_services) == 1 and _services[0].lower() == "all":
        _services = []

    override_default_versions_in_env(requested_services=_services)
    if randomize_ports:
        randomize_service_ports_env(_services)
    click.secho("Environment setup", fg="green")

    normalized_services = [normalize_service_name(s) for s in _services]
    services_up(
        services=normalized_services,
        filepath=services_ctx.filepath,
        project_name=project_name,
        wait=wait,
        retries=retries,
        verbose=services_ctx.verbose,
    )

    # update the environment with the services' actual public ports before the
    # `env_output()` logic kicks in, so that we get the correct ports printed
    for env_var_name, port in get_public_service_ports(
        services=normalized_services,
        filepath=services_ctx.filepath,
        project_name=project_name,
    ).items():
        os.environ[env_var_name] = port

    click.secho("Services up!", fg="green")


@cli.command()
@click.option(
    "--env-prefix",
    default="",
    type=str,
    help="Prefix to use for the exported environment variables.",
)
@click.option(
    "--project-name",
    default=None,
    type=str,
    help="Project name to use for the services.",
)
@env_output(env_set_command="unset")
@click.pass_obj
def down(services_ctx, project_name, env_prefix):
    """Shuts down the required services."""
    services_down(filepath=services_ctx.filepath, project_name=project_name)
    click.secho("Services down!", fg="green")


@cli.command()
@click.option(
    "--pretty",
    is_flag=True,
    help="Pretty-print the output.",
)
@click.pass_obj
def show_services(services_ctx, pretty):
    """Show the supported services with their default configuration."""
    serialized_services = {**SERVICES}
    for service in serialized_services.values():
        types = service.get("TYPE", [])
        service["TYPE"] = [t.value for t in types]

    click.echo(json.dumps(serialized_services, indent=2 if pretty else None))
