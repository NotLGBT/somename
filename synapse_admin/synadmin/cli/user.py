""" User-related CLI commands
"""

import re
import click
from click_option_group import optgroup, MutuallyExclusiveOptionGroup
from click_option_group import RequiredAnyOptionGroup

from synadmin import cli

@cli.root.group()
def user():
    """ List, add, modify, deactivate/erase users, reset passwords.
    """


@user.command(name="list")
@click.option(
    "--from", "-f", "from_", type=int, default=0, show_default=True,
    help="""Offset user listing by given number. This option is also used for
    pagination.""")
@click.option(
    "--limit", "-l", type=int, default=100, show_default=True,
    help="Limit user listing to given number")
@click.option(
    "--guests/--no-guests", "-g/-G", default=None, show_default=True,
    help="Show guest users.")
@click.option(
    "--deactivated", "-d", is_flag=True, default=False,
    help="Also show deactivated/erased users", show_default=True)
@click.option(
    "--admins/--non-admins", "-a/-A", default=None,
    help="""Whether to filter for admins, or non-admins. If not specified,
    no admin filter is applied.""")
@optgroup.group(
    "Search options",
    cls=MutuallyExclusiveOptionGroup,
    help="")
@optgroup.option(
    "--name", "-n", type=str,
    help="""Search users by name - filters to only return users with user ID
    localparts or displaynames that contain this value (localpart is the left
    part before the colon of the matrix ID (@user:server)""")
@optgroup.option(
    "--user-id", "-i", type=str,
    help="""Search users by ID - filters to only return users with Matrix IDs
    (@user:server) that contain this value""")
@click.pass_obj
def list_user_cmd(helper, from_, limit, guests, deactivated, name, user_id,
                  admins):
    """ List users, search for users.
    """
    mxid = helper.generate_mxid(user_id)
    users = helper.api.user_list(from_, limit, guests, deactivated, name,
                                 mxid, admins)
    if users is None:
        click.echo("Users could not be fetched.")
        raise SystemExit(1)
    if helper.output_format == "human":
        click.echo("Total users on homeserver (excluding deactivated): {}"
                   .format(users["total"]))
        if int(users["total"]) != 0:
            helper.output(users["users"])
        if "next_token" in users:
            click.echo("There are more users than shown, use '--from {}' "
                       .format(users["next_token"]) +
                       "to go to next page")
    else:
        helper.output(users)
        

@user.command()
@click.pass_obj
def logged_in(helper):
    user = helper.api.user
    mxid = helper.generate_mxid(user)
    return helper.api.logged_in(mxid)


@user.command()
@click.argument("user_id", type=str)
@click.option(
    "--gdpr-erase", "-e", is_flag=True, default=False,
    help="""Marks the user as GDPR-erased. This means messages sent by the
    user will still be visible by anyone that was in the room when these
    messages were sent, but hidden from users joining the room
    afterwards.""", show_default=True)
@click.pass_obj
@click.pass_context
def deactivate(ctx, helper, user_id, gdpr_erase):
    """ Deactivate or gdpr-erase a user. Provide matrix user ID (@user:server)
    as argument. It removes active access tokens, resets the password, and
    deletes third-party IDs (to prevent the user requesting a password
    reset).
    """
    click.echo("""
    Note that deactivating/gdpr-erasing a user leads to the following:
    - Removal from all joined rooms
    - Password reset
    - Deletion of third-party-IDs (to prevent the user requesting a password)
    """)
    mxid = helper.generate_mxid(user_id)
    ctx.invoke(user_details_cmd, user_id=mxid)
    ctx.invoke(membership, user_id=mxid)
    m_erase_or_deact = "gdpr-erase" if gdpr_erase else "deactivate"
    m_erase_or_deact_p = "gdpr-erased" if gdpr_erase else "deactivated"
    sure = (
        helper.no_confirm or
        click.prompt("Are you sure you want to {} this user? (y/N)"
                     .format(m_erase_or_deact),
                     type=bool, default=False, show_default=False)
    )
    if sure:
        deactivated = helper.api.user_deactivate(mxid, gdpr_erase)
        if deactivated is None:
            click.echo("User could not be {}.".format(m_erase_or_deact))
            raise SystemExit(1)
        if helper.output_format == "human":
            if deactivated["id_server_unbind_result"] == "success":
                click.echo("User successfully {}.".format(m_erase_or_deact_p))
            else:
                click.echo("Synapse returned: {}".format(
                           deactivated["id_server_unbind_result"]))
        else:
            helper.output(deactivated)
    else:
        click.echo("Abort.")


@user.command(name="password")
@click.argument("user_id", type=str)
@click.option(
    "--no-logout", "-n", is_flag=True, default=False,
    help="Don't log user out of all sessions on all devices.")
@click.option(
    "--password", "-p", prompt=True, hide_input=True,
    confirmation_prompt=True, help="New password.")
@click.pass_obj
def password_cmd(helper, user_id, password, no_logout):
    """ Change a user's password.

    To prevent the user from being logged out of all sessions use option -n.
    """
    mxid = helper.generate_mxid(user_id)
    changed = helper.api.user_password(mxid, password, no_logout)
    if changed is None:
        click.echo("Password could not be reset.")
        raise SystemExit(1)
    if helper.output_format == "human":
        if changed == {}:
            click.echo("Password reset successfully.")
        else:
            click.echo("Synapse returned: {}".format(changed))
    else:
        helper.output(changed)


@user.command()
@click.argument("user_id", type=str)
@click.option(
    "--aliases/--ids", is_flag=True, default=True,
    help="""Display rooms as canonical aliases or room
    ID's.  [default: aliases]""")
@click.pass_obj
def membership(helper, user_id, aliases):
    """ List all rooms a user is member of.

    Provide matrix user ID (@user:server) as argument.
    """
    mxid = helper.generate_mxid(user_id)
    joined_rooms = helper.api.user_membership(mxid, aliases,
                                              helper.matrix_api)
    if joined_rooms is None:
        click.echo("Membership could not be fetched.")
        raise SystemExit(1)

    if helper.output_format == "human":
        click.echo("User is member of {} rooms."
                   .format(joined_rooms["total"]))
        if int(joined_rooms["total"]) != 0:
            helper.output(joined_rooms["joined_rooms"])
    else:
        helper.output(joined_rooms)


@user.command(name="search")
@click.argument("search-term", type=str)
@click.option(
    "--from", "-f", "from_", type=int, default=0, show_default=True,
    help="""Offset user listing by given number. This option is also used
    for pagination.""")
@click.option(
    "--limit", "-l", type=int, default=100, show_default=True,
    help="Maximum amount of users to return.")
@click.pass_context
def user_search_cmd(ctx, search_term, from_, limit):
    """ A shortcut to \'synapseadmin user list -d -g -n <search-term>\'.

    Searches for users by name/matrix-ID, including deactivated users as well
    as guest users. Also, compared to the original command, a case-insensitive
    search is done.
    """
    click.echo("User search results for '{}':".format(search_term.lower()))
    ctx.invoke(list_user_cmd, from_=from_, limit=limit,
               name=search_term.lower(), deactivated=True, guests=True)
    click.echo("User search results for '{}':"
               .format(search_term.capitalize()))
    ctx.invoke(list_user_cmd, from_=from_, limit=limit,
               name=search_term.capitalize(), deactivated=True, guests=True)


@user.command(name="details")
@click.argument("user_id", type=str)
@click.pass_obj
def user_details_cmd(helper, user_id):
    """ View details of a user account.
    """
    mxid = helper.generate_mxid(user_id)
    click.echo(user_id)
    click.echo(mxid)
    user_data = helper.api.user_details(mxid)
    if user_data is None:
        click.echo("User details could not be fetched.")
        raise SystemExit(1)
    helper.output(user_data)


class UserModifyOptionGroup(RequiredAnyOptionGroup):
    @property
    def name_extra(self):
        return []


@user.command()
@click.argument("user_id", type=str)
@optgroup.group(cls=UserModifyOptionGroup)
@optgroup.option(
    "--password-prompt", "-p", is_flag=True,
    help="Set password interactively.")
@optgroup.option(
    "--password", "-P", type=str,
    help="Set password on command line.")
@optgroup.option(
    "--display-name", "-n", type=str,
    help="Set display name. defaults to the value of user_id")
@optgroup.option(
    "--threepid", "-t", type=str, multiple=True, nargs=2,
    help="""Set a third-party identifier (email address or phone number). Pass
    two arguments: `medium value` (eg. `--threepid email <user@example.org>`).
    This option can be passed multiple times, which allows setting multiple
    entries for a user. When modifying existing users, all threepids are
    replaced by what's passed in all given `--threepid` options. Threepids are
    used for several things: For use when logging in, as an alternative to the
    user id; in the case of email, as an alternative contact to help with
    account recovery, as well as to receive notifications of missed
    messages.""")
@optgroup.option(
    "--clear-threepids", is_flag=True, default=None,
    help="Remove all threepids of an existing user.")
@optgroup.option(
    "--avatar-url", "-v", type=str,
    help="""Set avatar URL. Must be a MXC URI
    (https://matrix.org/docs/spec/client_server/r0.6.0#matrix-content-mxc-uris)
    """)
@optgroup.option(
    "--admin/--no-admin", "-a/-u", default=None,
    help="""Grant user admin permission. Eg user is allowed to use the admin
    API.""", show_default=True,)
@optgroup.option(
    "--activate", "deactivation", flag_value="activate",
    help="""Re-activate user.""")
@optgroup.option(
    "--deactivate", "deactivation", flag_value="deactivate",
    help="""Deactivate user. Use with caution! Deactivating a user
    removes their active access tokens, resets their password, kicks them out
    of all rooms and deletes third-party identifiers (to prevent the user
    requesting a password reset). See also "user deactivate" command.""")
@optgroup.option(
    "--user-type", type=str, default=None, show_default=True,
    help="""Change the type of the user. Currently understood by the Admin API
    are 'bot' and 'support'. Use 'regular' to create a regular Matrix user
    (which effectively sets the user-type to 'null'). If the --user-type option
    is omitted when modifying an existing user, the user-type will not be
    manipulated. If the --user-type option is omitted when creating a new user,
    a regular user will be created.""")
@optgroup.option(
    "--lock/--unlock", "-l/-L", default=None, show_default=False,
    help="""Whether to lock or unlock the account, preventing or allowing
    logins respectively. Feature first present in Synapse 1.91.0.""")
@click.pass_obj
@click.pass_context
def modify(ctx, helper, user_id, password, password_prompt, display_name,
           threepid, clear_threepids, avatar_url, admin, deactivation,
           user_type, lock):
    """ Create or modify a local user. Provide matrix user ID (@user:server)
    as argument.
    """
    # sanity checks that can't easily be handled by Click.
    if password_prompt and password:
        click.echo("Use either '-p' or '-P secret', not both.")
        raise SystemExit(1)
    if deactivation == "deactivate" and (password_prompt or password):
        click.echo(
            "Deactivating a user and setting a password doesn't make sense.")
        raise SystemExit(1)

    mxid = helper.generate_mxid(user_id)
    click.echo("Current user account settings:")
    ctx.invoke(user_details_cmd, user_id=mxid)
    click.echo("User account settings to be modified:")
    for key, value in ctx.params.items():
        # skip these, they get special treatment or can't be changed
        if key in ["user_id", "password", "password_prompt",
                   "clear_threepids"]:
            continue
        if key == "threepid":
            if value == (('', ''),) or clear_threepids:
                click.echo("threepid: All entries will be cleared!")
                continue
            for t_key, t_val in value:
                click.echo(f"{key}: {t_key} {t_val}")
                if t_key not in ["email", "msisdn"]:
                    helper.log.warning(
                        f"{t_key} is probably not a supported medium "
                        "type. Threepid medium types according to the "
                        "current matrix spec are: email, msisdn.")
        elif key == "user_type" and value == 'regular':
            click.echo("user_type: null")
        elif value not in [None, {}, []]:  # only show non-empty (aka changed)
            click.echo(f"{key}: {value}")

    if password_prompt:
        if helper.no_confirm:
            click.echo("Password prompt not available in non-interactive "
                       "mode. Use -P.")
        else:
            password = click.prompt("Password", hide_input=True,
                                    confirmation_prompt=True)
    elif password:
        click.echo("Password will be set as provided on command line.")
    else:
        password = None
    sure = (
        helper.no_confirm or
        click.prompt("Are you sure you want to modify/create user? (y/N)",
                     type=bool, default=False, show_default=False)
    )
    if sure:
        modified = helper.api.user_modify(
            mxid,
            password,
            display_name,
            (('', ''),) if clear_threepids else threepid,
            avatar_url,
            admin,
            deactivation,
            'null' if user_type == 'regular' else user_type, lock
        )
        if modified is None:
            click.echo("User could not be modified/created.")
            raise SystemExit(1)
        if helper.output_format == "human":
            if modified != {}:
                helper.output(modified)
                click.echo("User successfully modified/created.")
            else:
                click.echo("Synapse returned: {}".format(modified))
        else:
            helper.output(modified)
    else:
        click.echo("Abort.")