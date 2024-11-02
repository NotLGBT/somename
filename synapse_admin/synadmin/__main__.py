"""Entry point for running synadm

This file allows execution without formal installation using
`python -m synadm`, which proves useful, for instance, in Debian GNU/Linux
packaging.
"""

from synadmin.cli import root

root()
