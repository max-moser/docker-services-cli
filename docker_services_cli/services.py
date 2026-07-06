# SPDX-FileCopyrightText: 2020 CERN.
# SPDX-FileCopyrightText: 2024 Graz University of Technology.
# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o.
# SPDX-FileCopyrightText: 2026 TU Wien.
# SPDX-License-Identifier: MIT

"""Services module."""

import time
from os import path
from subprocess import PIPE, Popen, check_call, run

import click

from .config import DOCKER_SERVICES_FILEPATH, MYSQL, SERVICE_TYPES, SERVICES


def _run_healthcheck_command(command, verbose=False):
    """Runs a given command, returns True if it succeeds, False otherwise."""
    p = Popen(command, stdout=PIPE, stderr=PIPE)
    output, error = p.communicate()
    output = output.decode("utf-8")
    error = error.decode("utf-8")
    if p.returncode == 0:
        if verbose:
            click.secho(output, fg="green")
        return True
    if p.returncode != 0:
        if verbose:
            click.secho(
                f"Healthcheck failed.\nOutput: {output}\nError:{error}", fg="red"
            )
        return False


def es_healthcheck(
    *args, filepath=DOCKER_SERVICES_FILEPATH, project_name=None, **kwargs
):
    """Check the Elasticsearch service's health."""
    verbose = kwargs["verbose"]

    try:
        port = get_public_service_ports(
            ["elasticsearch"], filepath=filepath, project_name=project_name
        )["ELASTICSEARCH_PORT"]
        return _run_healthcheck_command(
            ["curl", "-f", f"localhost:{port}/_cluster/health?wait_for_status=green"],
            verbose,
        )
    except Exception as e:
        print(e)
        return False


def os_healthcheck(
    *args, filepath=DOCKER_SERVICES_FILEPATH, project_name=None, **kwargs
):
    """Check the OpenSearch service's health."""
    verbose = kwargs["verbose"]

    try:
        port = get_public_service_ports(
            ["opensearch"], filepath=filepath, project_name=project_name
        )["OPENSEARCH_PORT"]
        return _run_healthcheck_command(
            ["curl", "-f", f"localhost:{port}/_cluster/health?wait_for_status=green"],
            verbose,
        )
    except Exception as e:
        print(e)
        return False


def postgresql_healthcheck(*args, **kwargs):
    """Postgresql healthcheck."""
    filepath = kwargs["filepath"]
    verbose = kwargs["verbose"]
    project_name = kwargs["project_name"]
    proj_name_args = ["--project-name", project_name] if project_name else []

    return _run_healthcheck_command(
        [
            "docker",
            "compose",
            *proj_name_args,
            "--file",
            filepath,
            "exec",
            "-T",
            "postgresql",
            "bash",
            "-c",
            "pg_isready",
        ],
        verbose,
    )


def mysql_healthcheck(*args, **kwargs):
    """Mysql healthcheck."""
    filepath = kwargs["filepath"]
    verbose = kwargs["verbose"]
    password = MYSQL["CONTAINER_CONFIG_ENVIRONMENT_VARIABLES"]["MYSQL_ROOT_PASSWORD"]
    project_name = kwargs["project_name"]
    proj_name_args = ["--project-name", project_name] if project_name else []

    return _run_healthcheck_command(
        [
            "docker",
            "compose",
            *proj_name_args,
            "--file",
            filepath,
            "exec",
            "-T",
            "mysql",
            "bash",
            "-c",
            f'mysql -p{password} -e "select Version();"',
        ],
        verbose,
    )


def rabbitmq_healthcheck(*args, **kwargs):
    """Rabbitmq healthcheck."""
    filepath = kwargs["filepath"]
    verbose = kwargs["verbose"]
    project_name = kwargs["project_name"]
    proj_name_args = ["--project-name", project_name] if project_name else []

    return _run_healthcheck_command(
        [
            "docker",
            "compose",
            *proj_name_args,
            "--file",
            filepath,
            "exec",
            "-T",
            "rabbitmq",
            "bash",
            "-c",
            "rabbitmq-diagnostics check_running",
        ],
        verbose,
    )


def redis_healthcheck(*args, **kwargs):
    """Redis healthcheck."""
    filepath = kwargs["filepath"]
    verbose = kwargs["verbose"]
    project_name = kwargs["project_name"]
    proj_name_args = ["--project-name", project_name] if project_name else []

    return _run_healthcheck_command(
        [
            "docker",
            "compose",
            *proj_name_args,
            "--file",
            filepath,
            "exec",
            "-T",
            "redis",
            "bash",
            "-c",
            "redis-cli ping",
            "|",
            "grep 'PONG'",
            "&>/dev/null;",
        ],
        verbose,
    )


def minio_healthcheck(*args, **kwargs):
    """Minio healthcheck."""
    verbose = kwargs["verbose"]

    return _run_healthcheck_command(
        ["curl", "-f", "http://localhost:9000/minio/health/live"], verbose
    )


HEALTHCHECKS = {
    "elasticsearch": es_healthcheck,
    "opensearch": os_healthcheck,
    "postgresql": postgresql_healthcheck,
    "mysql": mysql_healthcheck,
    "rabbitmq": rabbitmq_healthcheck,
    "redis": redis_healthcheck,
    "minio": minio_healthcheck,
}
"""Health check functions module path, as string."""


def wait_for_services(
    services,
    filepath=DOCKER_SERVICES_FILEPATH,
    project_name=None,
    max_retries=6,
    verbose=False,
):
    """Wait for services to be up.

    It performs configured healthchecks in a serial fashion, following the
    order given in the ``up`` command. If the services is an empty list, to be
    compliant with `docker compose` it will perform the healthchecks of all the
    services.
    """
    if len(services) == 0:
        services = HEALTHCHECKS.keys()

    for service in services:
        exp_backoff_time = 2
        try_ = 1
        # Using plain __import__ to avoid depending on invenio-base
        check = HEALTHCHECKS[service]
        ready = check(filepath=filepath, project_name=project_name, verbose=verbose)
        while not ready and try_ < max_retries:
            click.secho(
                f"{service} not ready at {try_} retries, waiting {exp_backoff_time}s",
                fg="yellow",
            )
            try_ += 1
            time.sleep(exp_backoff_time)
            exp_backoff_time *= 2
            ready = check(filepath=filepath, project_name=project_name, verbose=verbose)

        if not ready:
            click.secho(f"Unable to boot up {service}", fg="red")
            exit(1)
        else:
            click.secho(f"{service} up and running!", fg="green")


def services_up(
    services,
    filepath=DOCKER_SERVICES_FILEPATH,
    project_name=None,
    wait=True,
    retries=6,
    verbose=False,
):
    """Start the given services up.

    docker compose is smart about not rebuilding an image if
    there is no need to, so --build is not a slow default. In addition
    ``--detach`` is not supported in 1.17.0 or previous.
    """
    services = services or [
        service for _, services in SERVICE_TYPES.items() for service in services
    ]
    if not path.exists(filepath):
        click.secho(
            f"Filepath {filepath} for docker-services.yml file does not exist.",
            fg="red",
        )
        exit(1)

    proj_name_args = [] if not project_name else ["--project-name", project_name]
    command = ["docker", "compose", *proj_name_args, "--file", filepath, "up", "-d"]
    command.extend(services)

    check_call(command)
    if wait:
        wait_for_services(
            services,
            filepath,
            project_name=project_name,
            max_retries=retries,
            verbose=verbose,
        )


def services_down(filepath=DOCKER_SERVICES_FILEPATH, project_name=None):
    """Stops the given services.

    It does not requries the services. It stops containers and removes
    containers, networks, volumes, and images created by ``up``.
    """
    proj_name_args = [] if not project_name else ["--project-name", project_name]
    command = [
        "docker",
        "compose",
        *proj_name_args,
        "--file",
        filepath,
        "down",
        "--volumes",
    ]

    check_call(command)


def get_public_service_ports(
    services, filepath=DOCKER_SERVICES_FILEPATH, project_name=None
):
    """Get the actual ports assigned to the services, as reported by docker compose.

    This is useful when binding services to port 0, which assigns a randomly selected
    free port for the service.
    """
    actual_ports = {}
    proj_name_args = [] if not project_name else ["--project-name", project_name]
    base_command = ["docker", "compose", *proj_name_args, "--file", filepath, "port"]
    for service in services:
        for port_name, port_value in SERVICES[service].get("PORTS", {}).items():
            # we assume the internal port to be the same as the configured default port
            internal_port = str(port_value)

            command = base_command + [service, internal_port]
            completed_process = run(command, capture_output=True, check=True, text=True)

            # the public port will typically be reported together with the address,
            # e.g. 127.0.0.1:5432
            public_port = completed_process.stdout
            if ":" in public_port:
                *_, public_port = public_port.split(":")

            actual_ports[port_name] = public_port.strip()

    return actual_ports
