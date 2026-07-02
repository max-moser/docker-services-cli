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
"""

__version__ = "0.12.2"

__all__ = ("__version__",)
