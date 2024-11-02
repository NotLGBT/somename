"""Synapse Admin API and regular Matrix API clients

See https://github.com/matrix-org/synapse/tree/master/docs/admin_api for
documentation of the Synapse Admin APIs and the Matrix spec at
https://matrix.org/docs/spec/#matrix-apis.
"""

import requests
from http.client import HTTPConnection
import json
import re


class ApiRequest:
    """Basic API request handling and helper utilities"""

    def __init__(self, log, user, password, token, base_url, path, timeout, debug,
                verify):
        """Initialize an APIRequest object

        Args:
            log (logger object): an already initialized logger object
            user (string): the user with access to the API (currently unused).
                This can either be the fully qualified Matrix user ID, or just
                the localpart of the user ID.
            token (string): the API user's token
            base_url (string): URI e.g https://fqdn:port
            path (string): the path to the API endpoint; it's put after
                base_url to form the basis for all API endpoint paths
            timeout (int): requests module timeout used in query method
            debug (bool): enable/disable debugging in requests module
            verify(bool): SSL verification is turned on by default
                and can be turned off using this argument.
        """
        self.log = log
        self.password = password
        self.user = user
        self.token = token
        self.base_url = base_url.strip("/")
        self.path = path.strip("/")
        self.headers = {
            "Accept": "application/json",
            "Authorization": "Bearer " + self.token
        }
        self.timeout = timeout
        if debug:
            HTTPConnection.debuglevel = 1
        self.verify = verify

    def query(self, method, url, params=None, data=None):
        """Generic wrapper around requests methods.

        Handles requests methods, logging and exceptions, and URL encoding.

        Args:
            url (string): The path to the API endpoint.
            params (dict, optional): URL parameters (?param1&paarm2).  Defaults
                to None.
            data (dict, optional): Request body used in POST, PUT, DELETE
                requests.  Defaults to None.

        Returns:
            string or None: Usually a JSON string containing
                the response of the API; responses that are not 200(OK) (usally
                error messages returned by the API) will also be returned as
                JSON strings. On exceptions the error type and description are
                logged and None is returned.
        """

        try:
            #building url
            url = self.base_url + '/' + self.path + url
            resp = requests.request(
                method, url, headers=self.headers,
                params=params, json=data, verify=self.verify
            )
            if not resp.ok:
                print(f"returned status code {resp.status_code}")

            return resp.json()
        except Exception as error:
            print("%s while querying %s: %s",
                           type(error).__name__, error)
        return None


class MiscRequest(ApiRequest):
    """ Miscellaneous HTTP requests

    Inheritance:
        ApiRequest (object): parent class containing general properties and
            methods for requesting REST API's
    """
    def __init__(self, log, timeout, debug, verify=None):
        """Initialize the MiscRequest object

        Args:
            log (logger object): an already initialized logger object
            timeout (int): requests module timeout used in ApiRequest.query
                method
            debug (bool): enable/disable debugging in requests module
            verify(bool): SSL verification is turned on by default
                and can be turned off using this method.
        """
        super().__init__(
            log, "", "", "", # Set user and token to empty string
            "", "",  # Set base_url and path to empty string
            timeout, debug, verify
        )

    def federation_uri_well_known(self):
        """Retrieve the URI to the Server-Server (Federation) API port via the
        .well-known resource of a Matrix server/domain.

        Args:
            base_url: proto://name or proto://fqdn

        Returns:
            string: https://fqdn:port of the delegated server for Server-Server
                communication between Matrix homeservers or None on errors.
        """
        resp = self.query(
            "get", ".well-known/matrix/server"
        )
        if resp is not None:
            if ":" in resp["m.server"]:
                return "https://" + resp["m.server"]
            else:
                return "https://" + resp["m.server"] + ":8448"
        self.log.error(".well-known/matrix/server could not be fetched.")
        return None


class Matrix(ApiRequest):
    """ Matrix API client"""

    def __init__(self, log, user, password, token, base_url, matrix_path,
                 timeout, debug, verify):
        """Initialize the Matrix API object

        Args:
            log (logger object): an already initialized logger object
            user (string): the user with access to the Matrix API (currently
                unused); This can either be the fully qualified Matrix user ID,
                or just the localpart of the user ID.
            token (string): the Matrix API user's token
            base_url (string): URI e.g https://fqdn:port
            path (string): the path to the API endpoint; it's put after
                base_url and forms the basis for all API endpoint paths
            timeout (int): requests module timeout used in ApiRequest.query
                method
            debug (bool): enable/disable debugging in requests module
            verify(bool): SSL verification is turned on by default
                and can be turned off using this method.
        """
        super().__init__(
            log, user, password, token,
            base_url, matrix_path,
            timeout, debug, verify
        )
        self.user = user


    def user_login(self, user_id, password):
        """Login as a Matrix user and retrieve an access token

        Args:
            user_id (string): a fully qualified Matrix user ID
            password (string): the Matrix user's password

        Returns:
            string: JSON string containing a token suitable to access the
                Matrix API on the user's behalf, a device_id and some more
                details on Matrix server and user.
        """
        return self.query("post", "/client/r0/login", data={
            "password": password,
            "type": "m.login.password",
            "user": f"{user_id}",
            "initial_device_display_name": "synadm matrix login command"
        })
    

    def room_get_id(self, room_alias):
        """ Get the room ID for a given room alias

        Args:
            room_alias (string): A Matrix room alias (#name:example.org)

        Returns:
            string, dict or None: A dict containing the room ID for the alias.
                If room_id is missing in the response we return the whole
                response as it might contain Synapse's error message.
        """
        room_directory = self.query(
            "get", f"client/r0/directory/room/{room_alias}"
        )
        if "room_id" in room_directory:
            return room_directory["room_id"]
        else:
            return room_directory  # might contain useful error message


    def room_get_aliases(self, room_id):
        """ Get a list of room aliases for a given room ID

        Args:
            room_id (string): A Matrix room ID (!abc123:example.org)

        Returns:
            dict or None: A dict containing a list of room aliases, Synapse's
                error message or None on exceptions.
        """
        return self.query(
            "get", f"client/r0/rooms/{room_id}/aliases"
        )
    
    
    def room_create(self, room_name, topic, private = True):
        """
        Create a room with a given name

        Args:
            room_name (string): a name of Matrix room (MyRoom)
        
        Returns:
            dict or None: A dict containing <>, error message or None on exceptions
        """
        body = {
            "preset": "private_chat" if private else "public_chat",
            "name": room_name,
            "topic": topic,
            "creation_content": {
            "m.federate": False
            }
        }

        return self.query(
            "post", f"/client/r0/createRoom", data=body
        )


    def raw_request(self, endpoint, method, data, token=None):
        data_dict = {}
        if method != "get":
            self.log.debug("The data we are trying to parse and submit:")
            self.log.debug(data)
            try:  # user provided json might be crap
                data_dict = json.loads(data)
            except Exception as error:
                self.log.error("loading data: %s: %s",
                               type(error).__name__, error)
                return None

        return self.query(method, endpoint, data=data_dict)


    def server_name_keys_api(self, server_server_uri):
        """Retrieve the Matrix server's own homeserver name via the
        Server-Server (Federation) API.

        Args:
            server_server_uri (string): proto://name:port or proto://fqdn:port

        Returns:
            string: The Matrix server's homeserver name or FQDN, usually
            something like matrix.DOMAIN or DOMAIN
        """
        resp = self.query(
            "get", "key/v2/server", base_url_override=server_server_uri
        )
        if not resp or not resp.get("server_name"):
            self.log.error("The homeserver name could not be fetched via the "
                           "federation API key/v2/server.")
            return None
        return resp['server_name']


class SynapseAdmin(ApiRequest):
    """Synapse Admin API client"""

    def __init__(self, log, user, password, token, base_url, admin_path, timeout, debug,
                 verify):
        """Initialize the SynapseAdmin object

        Args:
            log (logger object): An already initialized logger object
            user (string): An admin-enabled Synapse user (currently unused).
                This can either be the fully qualified Matrix user ID,
                or just the localpart of the user ID.
            token (string): The admin user's token
            base_url (string): URI e.g https://fqdn:port
            path (string): The path to the API endpoint; it's put after
                base_url and the basis for all API endpoint paths
            timeout (int): Requests module timeout used in ApiRequest.query
                method
            debug (bool): enable/disable debugging in requests module
            verify(bool): SSL verification is turned on by default
                and can be turned off using this argument.
        """
        super().__init__(
            log, user, password, token,
            base_url, admin_path,
            timeout, debug, verify
        )
        self.user = user

    
    def logged_in(self, user):
        return self.query("get", f"/v1/whois/{user}")


    def user_list(self, _from, _limit, _guests, _deactivated,
                  _name, _user_id, _admin=None):
        """List and search users

        Args:
            _from (int): offsets user list by this number, used for pagination
            _limit (int): maximum number of users returned, used for pagination
            _guests (bool): enable/disable fetching of guest users
            _deactivated (bool): enable/disable fetching of deactivated users
            _name (string): user name localpart to search for, see Synapse
                Admin API docs for details
            _user_id (string): fully qualified Matrix user ID to search for
            _admin (bool or None): whether to filter for admins. a None
                does not filter.

        Returns:
            string: JSON string containing the found users
        """
        params = {
            "from": _from,
            "limit": _limit,
            "guests": (str(_guests).lower() if isinstance(_guests, bool)
                       else None),
            "deactivated": "true" if _deactivated else None,
            "name": _name,
            "user_id": _user_id
        }
        if _admin is not None:
            params["admins"] = str(_admin).lower()
        return self.query("get", "/v2/users", params=params)


    def user_list_paginate(self, _limit, _guests, _deactivated,
                           _name, _user_id, _from="0", admin=None):
        """Yields API responses for all of the pagination.

        Args:
            _limit (int): Maximum number of users returned, used for
                pagination.
            _guests (bool): Enable/disable fetching of guest users.
            _deactivated (bool): Enable/disable fetching of deactivated
                users.
            _name (string): User name localpart to search for, see Synapse
                Admin API docs for details.
            _user_id (string): Fully qualified Matrix user ID to search for.
            _from (string): Offsets user list by this number, used for
                pagination.

        Yields:
            dict: The Admin API response for listing accounts.
                https://element-hq.github.io/synapse/latest/admin_api/user_admin_api.html#list-accounts
        """
        while _from is not None:
            response = self.user_list(_from, _limit, _guests, _deactivated,
                                      _name, _user_id, admin)
            yield response
            _from = response.get("next_token", None)


    def user_membership(self, user_id, return_aliases, matrix_api):
        """Get a list of rooms the given user is member of

        Args:
            user_id (string): Fully qualified Matrix user ID
            room_aliases (bool): Return human readable room aliases instead of
                room ID's if applicable.
            matrix_api (object): An initialized Matrix object needs to be
                passes as we need some Matrix API functionality here.

        Returns:
            string: JSON string containing the Admin API's response or None if
                an exception occured. See Synapse Admin API docs for details.
        """

        rooms = self.query("get", f"/v1/users/{user_id}/joined_rooms")
        if return_aliases and rooms is not None and "joined_rooms" in rooms:
            for i, room_id in enumerate(rooms["joined_rooms"]):
                aliases = matrix_api.room_get_aliases(room_id)
                if aliases["aliases"] != []:
                    rooms["joined_rooms"][i] = " ".join(aliases["aliases"])
        return rooms


    def user_deactivate(self, user_id, gdpr_erase):
        """Delete a given user

        Args:
            user_id (string): fully qualified Matrix user ID
            gdpr_erase (bool): enable/disable gdpr-erasing the user, see
                Synapse Admin API docs for details.

        Returns:
            string: JSON string containing the Admin API's response or None if
                an exception occured. See Synapse Admin API docs for details.
        """
        return self.query("post", f"/v1/deactivate/{user_id}", data={
            "erase": gdpr_erase
        })


    def user_password(self, user_id, password, no_logout):
        """Set the user password, and log the user out if requested

        Args:
            user_id (string): fully qualified Matrix user ID
            password (string): new password that should be set
            no_logout (bool): the API defaults to logging out the user after
                password reset via the Admin API, this option can be used to
                disable this behaviour.

        Returns:
            string: JSON string containing the Admin API's response or None if
            an exception occured. See Synapse Admin API docs for details.
        """
        data = {"new_password": password}
        if no_logout:
            data.update({"logout_devices": False})
        return self.query("post", f"/v1/reset_password/{user_id}", data=data)


    def user_details(self, user_id):
        """Get information about a given user

        Note that the Admin API docs describe this function as "Query User
        Account".

        Args:
            user_id (string): fully qualified Matrix user ID

        Returns:
            string: JSON string containing the Admin API's response or None if
                an exception occured. See Synapse Admin API docs for details.

        """
        return self.query("get", f"/v2/users/{user_id}")


    def user_modify(self, user_id, password, display_name, threepid,
                    avatar_url, admin, deactivation, user_type, lock):
        """ Create or update information about a given user

        The threepid argument must be passed as a tuple in a tuple (which is
        what we usually get from a Click multi-arg option)
        """
        data = {}
        if password:
            data.update({"password": password})
        if display_name:
            data.update({"displayname": display_name})
        if threepid:
            if threepid == (('', ''),):  # empty strings clear all threepids
                data.update({"threepids": []})
            else:
                data.update({"threepids": [
                    {"medium": m, "address": a} for m, a in threepid
                ]})
        if avatar_url:
            data.update({"avatar_url": avatar_url})
        if admin is not None:
            data.update({"admin": admin})
        if lock is not None:
            data.update({"locked": lock})
        if deactivation == "deactivate":
            data.update({"deactivated": True})
        if deactivation == "activate":
            data.update({"deactivated": False})
        if user_type:
            data.update({"user_type": None if user_type == 'null' else
                         user_type})
        return self.query("put", f"/v2/users/{user_id}", data=data)

    
    def room_join(self, room_id_or_alias, user_id):
        """ Allow an administrator to join an user account with a given user_id
        to a room with a given room_id_or_alias
        """
        data = {"user_id": user_id}
        return self.query("post", f"/v1/join/{room_id_or_alias}", data=data)

    
    def room_list(self, _from, limit, name, order_by, reverse):
        """ List and search rooms
        """
        return self.query("get", "/v1/rooms", params={
            "from": _from,
            "limit": limit,
            "search_term": name,
            "order_by": order_by,
            "dir": "b" if reverse else None
        })

    
    def room_list_paginate(self, limit, name, order_by, reverse, _from=0):
        """ Yields API responses for room listing.

        Args:
            limit (int): Maximum number of rooms returned per pagination.
            name (string or None): Search for a room by name. Passed as
                `search_term` in the room list API. Use Python None to avoid
                searching.
            order_by (string): Synapse Room list API specific argument.
            reverse (bool): Whether the results should be
            _from (int): Initial offset in pagination.

        Yields:
            dict: The Admin API response for listing accounts.
                https://element-hq.github.io/synapse/latest/admin_api/rooms.html#list-room-api
        """
        while _from is not None:
            response = self.query("get", "/v1/rooms", params={
                "from": _from,
                "limit": limit,
                "search_term": name,
                "order_by": order_by,
                "dir": "b" if reverse else None
            })
            yield response
            _from = response.get("next_batch", None)
            self.log.debug(f"room_list_paginate: next from value = {_from}")

    
    def room_details(self, room_id):
        """ Get details about a room
        """
        return self.query("get", f"/v1/rooms/{room_id}")

    
    def room_members(self, room_id):
        """ Get a list of room members
        """
        return self.query("get", f"/v1/rooms/{room_id}/members")

    
    def room_delete(self, room_id, new_room_user_id, room_name, message,
                    block, no_purge, force_purge):
        """ Delete a room and purge it if requested
        """
        data = {
            "block": block,  # data with proper defaults from cli
            "purge": not bool(no_purge)  # should go here
        }
        # everything else is optional and shouldn't even exist in post body
        if new_room_user_id:
            data.update({"new_room_user_id": new_room_user_id})
        if room_name:
            data.update({"room_name": room_name})
        if message:
            data.update({"message": message})
        if force_purge:
            data.update({"force_purge": force_purge})
        return self.query("delete", f"/v1/rooms/{room_id}", data=data)

    
    def block_room(self, room_id, block):
        """ Block or unblock a room.

        Args:
            room_id (string): Required.
            block (boolean): Whether to block or unblock a room.

        Returns:
            string: JSON string containing the Admin API's response or None if
                an exception occurred. See Synapse Admin API docs for details.
        """
        # TODO prevent usage on versions before 1.48
        data = {
            "block": block
        }
        return self.query("put", f"/v1/rooms/{room_id}/block", data=data)

    
    def room_block_status(self, room_id):
        """ Returns if the room is blocked or not, and who blocked it.

        Args:
            room_id (string): Fully qualified Matrix room ID.

        Returns:
            string: JSON string containing the Admin API's response or None if
                an exception occured. See Synapse Admin API docs for details.
        """
        # TODO prevent usage on versions before 1.48
        return self.query("get", f"/v1/rooms/{room_id}/block")

    
    def room_make_admin(self, room_id, user_id):
        """ Grant a user room admin permission. If the user is not in the room,
        and it is not publicly joinable, then invite the user.
        """
        data = {}
        if user_id:
            data.update({"user_id": user_id})
        return self.query("post", f"/v1/rooms/{room_id}/make_room_admin", data=data)

    
    def version(self):
        """ Get the server version
        """
        return self.query("get", "/v1/server_version")

    
    def group_delete(self, group_id):
        """ Delete a local group (community)
        """
        return self.query("post", f"/v1/delete_group/{group_id}")
    

    def notice_send(self, receivers, content_plain, content_html, paginate,
                    regex):
        """ Send server notices.

        Args:
            receivers (string): Target(s) of the notice. Either localpart or
                regular expression matching localparts.
            content_plain (string): Unformatted text of the notice.
            content_html (string): HTML-formatted text of the notice.
            paginate (int): Limits to how many users the notice is sent at
                once.  Users are fetched with the user_list method and using
                its pagination capabilities.
            to_regex (bool): Selects whether receivers should be interpreted as
                a regular expression or a single recipient.

        Returns:
            list: A list of dictionaries, each containing the response of
                what a single notice Admin API call returned. Usually that is
                an event ID or an error. See Synapse Admin API docs for
                details.
        """
        data = {
            "user_id": "",
            "content": {
                "msgtype": "m.text",
                "body": content_plain,
                "format": "org.matrix.custom.html",
                "formatted_body": content_html
            }
        }

        if regex:
            outputs = []
            response = self.user_list(0, paginate, True, False, "", "", None)
            if "users" not in response:
                return
            while True:
                for user in response["users"]:
                    if re.match(receivers, user["name"]):
                        data["user_id"] = user["name"]
                        outputs.append(
                            self.query(
                                "post", "/v1/send_server_notice", data=data
                            )
                        )

                if "next_token" not in response:
                    return outputs
                response = self.user_list(response["next_token"],
                                          100, True, False, "", "", None)
        else:
            data["user_id"] = receivers
            return [self.query("post", "/v1/send_server_notice", data=data)]

    
    def raw_request(self, endpoint, method, data):
        data_dict = {}
        if method != "get":
            self.log.debug("The data we are trying to parse and submit:")
            self.log.debug(data)
            try:
                data_dict = json.loads(data)
            except Exception as error:
                self.log.error("loading data: %s: %s",
                               type(error).__name__, error)
                return None

        return self.query(method, endpoint, data=data_dict)