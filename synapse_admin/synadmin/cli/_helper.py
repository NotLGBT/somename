""" CLI helpers and utilities"""

import os
import logging
import pprint
import json
import click
import yaml
import tabulate
import re

from synadmin import api


def humanize(data):
    """ Try to display data in a human-readable form:
    - Lists of dicts are displayed as tables.
    - Dicts are displayed as pivoted tables.
    - Lists are displayed as a simple list.
    """
    if isinstance(data, list) and len(data):
        if isinstance(data[0], dict):
            headers = {header: header for header in data[0]}
            return tabulate.tabulate(data, tablefmt="simple", headers=headers)
    if isinstance(data, list):
        return "\n".join(data)
    if isinstance(data, dict):
        return tabulate.tabulate(data.items(), tablefmt="plain")
    return str(data)


class APIHelper:
    """ API client enriched with CLI-level functions, used as a proxy to the
    client object.
    """

    FORMATTERS = {
        "pprint": pprint.pformat,
        "json": lambda data: json.dumps(data, indent=4),
        "minified": lambda data: json.dumps(data, separators=(",", ":")),
        "yaml": yaml.dump,
        "human": humanize
    }

    CONFIG = {
        "user": "",
        "password": "",
        "token": "",
        "base_url": "http://localhost:8008",
        "admin_path": "/_synapse/admin",
        "matrix_path": "/_matrix",
        "timeout": 30,
        "homeserver": "",
        "ssl_verify": True
    }

    def __init__(self, config_path, verbose, no_confirm, output_format_cli):
        self.config = APIHelper.CONFIG.copy()
        self.config_path = os.path.expanduser(config_path)
        self.no_confirm = no_confirm
        self.api = None
        self.init_logger(verbose)
        self.requests_debug = False
        if verbose >= 3:
            self.requests_debug = True
        self.output_format_cli = output_format_cli  # override from cli

    
    def init_logger(self, verbose):
        """ Log both to console (defaults to WARNING) and file (DEBUG).
        """
        log_path = os.path.expanduser("~/.local/share/synapseadmin/debug.log")
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        log = logging.getLogger("synapseadmin")
        log.setLevel(logging.DEBUG)
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(
            logging.DEBUG if verbose > 1 else
            logging.INFO if verbose == 1 else
            logging.WARNING
        )
        file_formatter = logging.Formatter(
            "%(asctime)s %(name)-8s %(levelname)-7s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_formatter = logging.Formatter("%(levelname)-5s %(message)s")
        console_handler.setFormatter(console_formatter)
        file_handler.setFormatter(file_formatter)
        log.addHandler(console_handler)
        log.addHandler(file_handler)
        self.log = log

    def _set_formatter(self, _output_format):
        for name, formatter in APIHelper.FORMATTERS.items():
            if name.startswith(_output_format):
                self.output_format = name
                self.formatter = formatter
                break
        self.log.debug("Formatter in use: %s - %s", self.output_format,
                       self.formatter)
        return True

    def load(self):
        """ Load the configuration and initialize the client.
        """
        try:
            with open(self.config_path) as handle:
                self.config.update(yaml.load(handle, Loader=yaml.SafeLoader))
        except Exception as error:
            self.log.error("%s while reading configuration file", error)
        for key, value in self.config.items():

            if key == "ssl_verify" and not isinstance(value, bool):
                self.log.error("Config value error: %s, %s must be boolean",
                               key, value)

            if not value and not isinstance(value, bool):
                self.log.error("Config entry missing: %s, %s", key, value)
                return False
            else:
                if key == "token":
                    self.log.debug("Config entry read. %s: REDACTED", key)
                else:
                    self.log.debug("Config entry read. %s: %s", key, value)
        if self.output_format_cli:  # we have a cli output format override
            self._set_formatter(self.output_format_cli)
        else:  # we use the configured default output format
            self._set_formatter(self.config["format"])
        self.api = api.SynapseAdmin(
            self.log,
            self.config["user"], self.config["password"],
            self.config["token"], self.config["base_url"],
            self.config["admin_path"], self.config["timeout"],
            self.requests_debug, self.config["ssl_verify"]
        )
        self.matrix_api = api.Matrix(
            self.log,
            self.config["user"], self.config["password"],
            self.config["token"], self.config["base_url"], 
            self.config["matrix_path"], self.config["timeout"],
            self.requests_debug, self.config["ssl_verify"]
        )
        self.misc_request = api.MiscRequest(
            self.log,
            self.config["timeout"], self.requests_debug,
            self.config["ssl_verify"]
        )
        return True

    
    def write_config(self, config):
        """ Write a new version of the configuration to file.
        """
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, "w") as handle:
                yaml.dump(config, handle, default_flow_style=False,
                          allow_unicode=True)
            if os.name == "posix":
                click.echo("Restricting access to config file to user only.")
                os.chmod(self.config_path, 0o600)
            else:
                click.echo(f"Unsupported OS, please adjust permissions of "
                           f"{self.config_path} manually")

            return True
        except Exception as error:
            self.log.error("%s trying to write configuration", error)
            return False

    def output(self, data):
        """ Output data object using the configured formatter.
        """
        click.echo(self.formatter(data))


    def refresh_token(self):
        """ retrieve user token
        """
        response = self.matrix_api.user_login(self.config['user'], self.config['password'])
        self.config['token'] = response['access_token']
        self.write_config(self.config)
        self.load()
        return response


    def generate_mxid(self, user_id):
        """ Checks whether the given user ID is an MXID already or else
        generates it from the passed string and the homeserver name fetched
        via the retrieve_homeserver_name method.

        Args:
            user_id (string): User ID given by user as command argument.

        Returns:
            string: the fully qualified Matrix User ID (MXID) or None if the
                user_id parameter is None or no regex matched.
        """
        if user_id is None:
            self.log.debug("Missing input in generate_mxid().")
            return None
        elif re.match(r"^@[-./=\w]+:[-\[\].:\w]+$", user_id):
            self.log.debug("A proper MXID was passed.")
            return user_id
        elif re.match(r"^@?[-./=\w]+:?$", user_id):
            self.log.debug("A proper localpart was passed, generating MXID "
                           "for local homeserver.")
            localpart = re.sub("[@:]", "", user_id)
            mxid = "@{}:{}".format(localpart, self.config["homeserver"])
            return mxid
        else:
            self.log.error("Neither an MXID nor a proper localpart was "
                           "passed.")
            return None
