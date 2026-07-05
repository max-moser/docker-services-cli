# SPDX-FileCopyrightText: 2020-2025 CERN.
# SPDX-FileCopyrightText: 2024 Graz University of Technology.
# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o.
# SPDX-FileCopyrightText: 2026 TU Wien.
# SPDX-License-Identifier: MIT

"""Configuration module.

Configuration values (e.g. service configuration) need to be set through
environment variables. However, sane defaults are provided below.

The list of services to be configured is taken from ``SERVICES``. Each one
should contain a ``<SERVICE_NAME>_VERSION`` variable.

Service's version are treated slightly different:

- If the variable is not found in the environment, it will use the set default.
- If the variable is set with a version number (e.g. 10, 10.7) it will use
  said value.
- If the variable is set with a string point to one of the configured
  ``latests`` it will load the value of said ``latest`` and use it.

This means that the environment set/load logic will first set the default
versions before loading a given service's version.
"""

from enum import Enum


class ServiceType(Enum):
    """Enum with the various known service types."""

    search = "search"
    database = "db"
    cache = "cache"
    message_queue = "mq"
    s3 = "s3"


DOCKER_SERVICES_FILEPATH = "docker-services.yml"
"""Docker services file default path."""

ELASTICSEARCH = {
    "ELASTICSEARCH_VERSION": "ELASTICSEARCH_7_LATEST",
    "DEFAULT_VERSIONS": {
        "ELASTICSEARCH_7_LATEST": "7.10.2",  # the last of the OSS versions (https://github.com/elastic/elasticsearch/issues/58303)
    },
    "CONTAINER_CONNECTION_ENVIRONMENT_VARIABLES": {
        "search": {
            "SEARCH_HOSTS": "\"[{'host': 'localhost', 'port': {ELASTICSEARCH_PORT}}]\"",
        }
    },
    "PORTS": {
        "ELASTICSEARCH_PORT": 9200,
        "ELASTICSEARCH_CLUSTER_PORT": 9300,
    },
    "TYPE": [ServiceType.search],
}
"""Elasticsearch service configuration."""

OPENSEARCH = {
    "OPENSEARCH_VERSION": "OPENSEARCH_2_LATEST",
    "DEFAULT_VERSIONS": {
        "OPENSEARCH_1_LATEST": "1.3.18",
        "OPENSEARCH_2_LATEST": "2.16.0",
    },
    "CONTAINER_CONNECTION_ENVIRONMENT_VARIABLES": {
        "search": {
            "SEARCH_HOSTS": "\"[{'host': 'localhost', 'port': {OPENSEARCH_PORT}}]\"",
        }
    },
    "PORTS": {
        "OPENSEARCH_PORT": 9200,
        "OPENSEARCH_CLUSTER_PORT": 9300,
    },
    "TYPE": [ServiceType.search],
}
"""Opensearch service configuration."""

POSTGRESQL = {
    "POSTGRESQL_VERSION": "POSTGRESQL_16_LATEST",
    "DEFAULT_VERSIONS": {
        "POSTGRESQL_14_LATEST": "14.9",
        "POSTGRESQL_15_LATEST": "15.4",
        "POSTGRESQL_16_LATEST": "16.2",
    },
    "CONTAINER_CONFIG_ENVIRONMENT_VARIABLES": {
        "POSTGRESQL_USER": "invenio",
        "POSTGRESQL_PASSWORD": "invenio",
        "POSTGRESQL_DB": "invenio",
    },
    "CONTAINER_CONNECTION_ENVIRONMENT_VARIABLES": {
        "db": {
            "SQLALCHEMY_DATABASE_URI": "postgresql+psycopg2://invenio:invenio@localhost:{POSTGRESQL_PORT}/invenio"
        }
    },
    "PORTS": {
        "POSTGRESQL_PORT": 5432,
    },
    "TYPE": [ServiceType.database],
}
"""Postgresql service configuration."""

MYSQL = {
    "MYSQL_VERSION": "MYSQL_8_LATEST",
    "DEFAULT_VERSIONS": {"MYSQL_8_LATEST": "8.3"},
    "CONTAINER_CONFIG_ENVIRONMENT_VARIABLES": {
        "MYSQL_USER": "invenio",
        "MYSQL_PASSWORD": "invenio",
        "MYSQL_DB": "invenio",
        "MYSQL_ROOT_PASSWORD": "invenio",
    },
    "CONTAINER_CONNECTION_ENVIRONMENT_VARIABLES": {
        "db": {
            "SQLALCHEMY_DATABASE_URI": "mysql+pymysql://invenio:invenio@localhost:{MYSQL_PORT}/invenio"
        }
    },
    "PORTS": {
        "MYSQL_PORT": 3306,
    },
    "TYPE": [ServiceType.database],
}
"""MySQL service configuration."""

REDIS = {
    "REDIS_VERSION": "REDIS_7_LATEST",
    "DEFAULT_VERSIONS": {
        "REDIS_6_LATEST": "6",
        "REDIS_7_LATEST": "7",
    },
    "CONTAINER_CONNECTION_ENVIRONMENT_VARIABLES": {
        "mq": {"BROKER_URL": "redis://localhost:{REDIS_PORT}/0"},
        "cache": {
            "CACHE_TYPE": "redis",
            "CACHE_REDIS_URL": "redis://localhost:{REDIS_PORT}/0",
        },
    },
    "PORTS": {
        "REDIS_PORT": 6379,
    },
    "TYPE": [ServiceType.cache, ServiceType.message_queue],
}
"""Redis service configuration."""

RABBITMQ = {
    "RABBITMQ_VERSION": "RABBITMQ_3_LATEST",
    "DEFAULT_VERSIONS": {"RABBITMQ_3_LATEST": "3"},
    "CONTAINER_CONNECTION_ENVIRONMENT_VARIABLES": {
        "mq": {"BROKER_URL": "amqp://localhost:{RABBITMQ_PORT}//"}
    },
    "PORTS": {
        "RABBITMQ_PORT": 5672,
        "RABBITMQ_MANAGEMENT_PORT": 15672,
    },
    "TYPE": [ServiceType.message_queue],
}
"""RabbitMQ service configuration."""

MINIO = {
    "MINIO_VERSION": "MINIO_2025_LATEST",
    # note: minio does not do semantic versioning, so we use the latest version
    # the release at the time of writing this is RELEASE.2025-02-28T09-55-16Z
    "DEFAULT_VERSIONS": {"MINIO_2025_LATEST": "latest"},
    "CONTAINER_CONFIG_ENVIRONMENT_VARIABLES": {
        "S3_ACCESS_KEY_ID": "invenio",
        # minio needs at least 8 characters for the secret
        "S3_SECRET_ACCESS_KEY": "invenio8",
    },
    "CONTAINER_CONNECTION_ENVIRONMENT_VARIABLES": {
        "s3": {
            "S3_ENDPOINT_URL": "http://localhost:{MINIO_PORT}",
            "S3_ACCESS_KEY_ID": "invenio",
            # minio needs at least 8 characters for the secret
            "S3_SECRET_ACCESS_KEY": "invenio8",
        }
    },
    "PORTS": {
        "MINIO_PORT": 9000,
        "MINIO_CONSOLE_PORT": 9001,
    },
    "TYPE": [ServiceType.s3],
}
"""MINIO service configuration."""

SERVICES = {
    "elasticsearch": ELASTICSEARCH,
    "opensearch": OPENSEARCH,
    "postgresql": POSTGRESQL,
    "mysql": MYSQL,
    "redis": REDIS,
    "rabbitmq": RABBITMQ,
    "minio": MINIO,
}
"""List of services to configure."""

SERVICES_ALL_DEFAULT_VERSIONS = {
    name: version
    for service in SERVICES.values()
    for name, version in service.get("DEFAULT_VERSIONS", {}).items()
}
"""Services default latest versions.

E.g.: ``{'ELASTICSEARCH_7_LATEST': '7.10.2', 'MINIO_2025_LATEST': 'latest', ...}``
"""

SERVICE_TYPES = {
    st.value: [name for name, config in SERVICES.items() if st in config["TYPE"]]
    for st in ServiceType
}
"""Types of offered services.

E.g.: ``{'search': ['elasticsearch', 'opensearch'], 's3': ['minio'], ...}``
"""
