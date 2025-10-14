..
    Copyright (C) 2020-2024 CERN.
    Copyright (C) 2023 Graz University of Technology.
    Copyright (C) 2024 TU Wien.

    Docker-Services-CLI is free software; you can redistribute it and/or modify
    it under the terms of the MIT License; see LICENSE file for more details.

Changes
=======

Version v0.12.1 (released 2025-10-14)

- fix: bind `127.0.0.1` by default for service ports
    * Binds `127.0.0.1` as the host IP for all mapped service ports.
    * Allows overriding the host IP using the `DOCKER_SERVICES_IP_BIND`
      environment variable.

Version v0.12.0 (released 2025-04-11)

- config: export `SEARCH_HOSTS` environment for OpenSearch/ElasticSearch

Version v0.11.1 (released 2025-04-11)

- Fix incomplete revert of port config change

Version 0.11.0 (released 2025-04-11)

- Postgresql: add 16 and remove 11, 12, 13
- mysql: remove 5, REASON: endoflife
- config: export SEARCH_HOSTS environment for OpenSearch/ElasticSearch
- feature: s3 support
    - This feature sets up a MinIO S3 server and creates
      a bucket named 'default' within it.
- env: better handling for "latest" version values

Version 0.10.1 (released 2024-08-23)

- Adds the missing OPENSEARCH_INITIAL_ADMIN_PASSWORD env var for newer versions
  of OpenSearch

Version 0.10.0 (released 2024-08-23)

- Updates OpenSearch versions

Version 0.9.0 (released 2024-06-27)

- Updates Python requirements
- Updates test dependencies
- Upgrades GitHub actions
- Removes version from docker compose files

Version 0.8.0 (released 2023-12-11)

- docker: move to docker compose v2

Version 0.7.1 (released 2023-09-05)

- Revert Postgres v11 version to stick to the one published on DockerHub
  without the leading `-<debian version>` tagging

Version 0.7.0 (released 2023-09-02)

- Upgrades Postgres and MySQL versions

Version 0.6.1 (released 2023-03-20)

- Adds back support for Python 3.6

Version 0.6.0 (released 2022-10-03)

- Adds OpenSearch v2

Version 0.5.0 (released 2022-08-30)

- Adds OpenSearch v1
- Removes Elasticsearch 6

Version 0.4.2 (released 2022-08-17)

- Upgrades Redis and MQ to latest version
- Supports min version of Python to 3.7
- Formats code with Black

Version 0.4.1 (released 2022-02-23)

- Removes upper bound on Click which causes projects where docker-services-cli
  is installed to limit Celery to v5.1.x because Celery v5.2 requires Click 8+.

Version 0.4.0 (released 2022-02-15)

- Changes default version of Postgres to v12.
- Adds Postgres v14 and upgrades other versions.

Version 0.3.1 (released 2021-08-04)

- Fixes an issue where created volumes were not removed again.
