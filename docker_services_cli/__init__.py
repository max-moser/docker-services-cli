# SPDX-FileCopyrightText: 2020-2025 CERN.
# SPDX-FileCopyrightText: 2022 University Münster.
# SPDX-FileCopyrightText: 2022-2026 TU Wien.
# SPDX-FileCopyrightText: 2023 Graz University of Technology.
# SPDX-License-Identifier: MIT

"""Module to ease the creation and management of services.

The specific version for the services can be set through environment variables

.. code-block:: console

    $ export OPENSEARCH_VERSION=2.16.0

It can also use the centrally managed (supported) major version:

.. code-block:: console

    $ export OPENSEARCH_VERSION=OPENSEARCH_2_LATEST

Then it simply needs to boot up the services. Note that if no version was
exported in the environment, the CLI will use the default values set in
``env.py``.

.. code-block:: console

    $ docker-services-cli up --search opensearch --db postgresql --cache redis

And turn them of once they are not needed anymore:

.. code-block:: console

    $ docker-services-cli down

Specific non-standard ports for each service can be used by providing them via
environment variables:

.. code-block:: console

    $ export OPENSEARCH_PORT=1234 OPENSEARCH_CLUSTER_PORT=9301 POSTGRESQL_PORT=1337
    $ REDIS_PORT=1993 docker-services-cli up --search opensearch --db postgresql --cache redis

Note that port 0 is a special value on Unix systems, which assigns a random free port!
The CLI provides a ``--randomize-ports`` flag to do this automatically.

The available services with their configuration can be displayed via the CLI:

.. code-block:: console

    $ docker-services-cli show-services
"""

__version__ = "0.12.2"

__all__ = ("__version__",)
