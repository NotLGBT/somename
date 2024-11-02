""" CLI commands executing regular Matrix API calls
"""

import click

from synadmin import cli
from synadmin.cli._common import common_opts_raw_command, data_opts_raw_command
from click_option_group import optgroup, MutuallyExclusiveOptionGroup


@cli.root.group()
def matrix():
    """ Execute Matrix API calls.
    """


@matrix.command(name="login")
@click.option(
    "-user_id", "-u", type=str, help="user_id in homeserver.")
@click.option(
    "--password", "-p", type=str,
    help="""The Matrix user's password.""")
@click.pass_obj
def login_cmd(helper, user_id, password):
    """ Login to Matrix via username/password and receive an access token.

    The response also contains a newly generated device ID and further
    information about user and homeserver.

    Each successful login will show up in the user's devices list marked
    with a display name of 'synapseadmin matrix login command'.
    """
    print(user_id, password)
    if not password and not user_id:
        login = helper.refresh_token()
    else:
        mxid = helper.generate_mxid(user_id)
        login = helper.matrix_api.user_login(mxid, password)

    if helper.no_confirm:
        if login is None:
            raise SystemExit(1)
        helper.output(login)
    else:
        if login is None:
            click.echo("Matrix login failed.")
            raise SystemExit(1)
        else:
            helper.output(login)


@matrix.command(name="raw")
@common_opts_raw_command
@data_opts_raw_command
@optgroup.group(
    "Matrix token",
    cls=MutuallyExclusiveOptionGroup,
    help="")
@optgroup.option(
    "--token", "-t", type=str, envvar='MTOKEN', show_default=True,
    help="""Token used for Matrix authentication instead of the configured
    admin user's token. If ``--token`` (and ``--prompt``) option is missing,
    the token is read from environment variable ``$MTOKEN`` instead. To make
    sure a user's token does not show up in system logs, don't provide it on
    the shell directly but set ``$MTOKEN`` with shell command ``read
    MTOKEN``.""")
@optgroup.option(
    "--prompt", "-p", is_flag=True, show_default=True,
    help="""Prompt for the token used for Matrix authentication. This option
    always overrides $MTOKEN.""")
@click.pass_obj
def raw_request_cmd(helper, endpoint, method, data, data_file, token, prompt):
    """ Execute a custom request to the Matrix API.

    The endpoint argument is the part of the URL _after_ the configured base
    URL (actually "Synapse base URL") and "Matrix API path" (see ``synapseadmin
    config``). A get request could look like this: ``synapseadmin matrix raw
    client/versions`` URL encoding must be handled at this point. Consider
    enabling debug outputs via synapseadmin's global flag ``-vv``

    Use either ``--token`` or ``--prompt`` to provide a user's token and
    execute Matrix commands on their behalf. Respect the privacy of others!
    Act responsible!

    \b
    The precedence rules for token reading are:
    1. Interactive input using ``--prompt``;
    2. Set on CLI via ``--token``
    3. Read from environment variable ``$MTOKEN``;
    4. Preconfigured admin token set via ``synapseadmin config``.

    Caution: Passing secrets as CLI arguments or via environment variables is
    not considered secure. Know what you are doing!
    """
    if prompt:
        token = click.prompt("Matrix token", type=str)

    if data_file:
        data = data_file.read()

    raw_request = helper.matrix_api.raw_request(endpoint, method, data,
                                                token=token)

    if helper.no_confirm:
        if raw_request is None:
            raise SystemExit(1)
        helper.output(raw_request)
    else:
        if raw_request is None:
            click.echo("The Matrix API's response was empty or JSON data "
                       "could not be loaded.")
            raise SystemExit(1)
        else:
            helper.output(raw_request)
