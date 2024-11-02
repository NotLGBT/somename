"""This module holds the `raw` command only."""

import click

from synadmin import cli
from synadmin.cli._common import common_opts_raw_command, data_opts_raw_command


@cli.root.command(name="raw")
@common_opts_raw_command
@data_opts_raw_command
@click.pass_obj
def raw_request_cmd(helper, endpoint, method, data, data_file):
    """ Issue a custom request to the Synapse Admin API.

    The endpoint argument is the part of the URL _after_ the configured
    "Synapse base URL" and "Synapse Admin API path" (see ``synapseadmin config``).
    A get request to the "Query User Account API" would look like this:
    ``synapseadmin raw v2/users/%40testuser%3Aexample.org``. URL encoding must be
    handled at this point. Consider enabling debug outputs via synapseadmin's global
    flag ``-vv``
    """
    if data_file:
        data = data_file.read()

    raw_request = helper.api.raw_request(endpoint, method, data)

    if helper.no_confirm:
        if raw_request is None:
            raise SystemExit(1)
        helper.output(raw_request)
    else:
        if raw_request is None:
            click.echo("The Admin API's response was empty or JSON data "
                       "could not be loaded.")
            raise SystemExit(1)
        else:
            helper.output(raw_request)
