# the Matrix-Synapse admin CLI
This CLI tool offers functionalities similar to the Synapse Admin API via terminal. It provides a simplified method to interact with the homeserver, perform routine administrative tasks. With CLI tool you can streamline server management tasks and automate repetitive operations.

### Usage 
```bash
synadmin [OPTIONS] COMMAND [ARGS]...
```

### Options:

  - `--version`                       Show the version and exit.
  
  - `-o, --output [yaml|json|minified|human|pprint|y|j|m|h|p|]`                               Override default output format. The 'human' mode gives a tabular or list view depending on the fetched data. 'json' returns formatted json. 'pprint' shows a formatted output with the help of Python's built-in pprint module. 'yaml' is a compromise between human- and machine-readable output.
                                  
  - `-c, --config-file PATH`          Configuration file path.  [default: ~/.config/synadmin.yaml]
  
  - `-h, --help`                      Show help message.

### Commands
 * [`config`](#config)   Modify synadmin's configuration.
 * [`group`](#group)    Manage groups (communities).
 * [`matrix`](#matrix)   Execute Matrix API calls.
 * [`notice`](#notice)   Send messages to users.
 * [`raw`](#raw)      Issue a custom request to the Synapse Admin API.
 * [`room`](#room)     Manipulate rooms and room membership.
 * [`user`](#user)     List, add, modify, deactivate/erase users, reset passwords.
 * `version`  Get the Synapse server version.

<a id="config"></a>
## Config
### Usage
```bash
synadmin config [OPTIONS]
```
Modify synadmin's configuration.
Configuration details are generally always asked interactively. Command line
options override the suggested defaults in the prompts.

### Options
  - `-u, --user TEXT`                 Admin user allowed to access the Synapse Admin API's.
  - `-t, --token TEXT`                The Admin user's access token.
  - `-b, --base-url TEXT`             The base URL Synapse is running on. It might be something like this: https://example.org
  - `-p, --admin-path TEXT`           The path Synapse provides its Admin API's, usually the default fits most installations.
  - `-m, --matrix-path TEXT`          The path Synapse provides the regular Matrix API's, usually the default fits most installations.
  - `-w, --timeout INTEGER`           The time in seconds synadmin should wait for responses from admin API's or Matrix API's. The default is 7 seconds.
  - `-o, --output [yaml|json|minified|human|pprint]` How synadmin displays data by default. The 'human' mode gives a tabular or list, 'json' returns formatted json. 'pprint' shows a formatted output with the help of Python's built-in pprint module. 'yaml' is a compromise between human- and machine-readable output   
  - `-n, --homeserver TEXT`           Synapse homeserver hostname. Usually matrix.DOMAIN or DOMAIN.
  - `-i, --ssl-verify`                Whether or not SSL certificates should be verified. Set to False to allow self-signed certifcates.
  - `-h, --help`                      Show usage message.

## User
### Usage
```bash
synadmin user [OPTIONS] COMMAND [ARGS]...
```
  List, add, modify, deactivate/erase users, reset passwords.

### Options
  `-h, --help`
  Show usage message.

### User-Commands
  * [`deactivate`](#user-deactivate)  Deactivate or erase a user.
  * [`details`](#user-details)     View details of a user account.
  * [`list`](#user-list)       List users, search for users.
  * [`membership`](#user-membership)  List all rooms a user is member of.
  * [`modify`](#user-modify)      Create or modify a local user.
  * [`password`](#user-password)    Change a user's password.
  * [`search`](#user-search)      A shortcut to 'synadmin user list -d -g -n <search-term>'.

<a id="user-deactivate"></a>
#### deactivate
```bash
synadmin user deactivate [OPTIONS] USER_ID
```

Deactivate or erase a user. Provide matrix user ID (@user:server) as
argument. It removes active access tokens, resets the password.

* Options
  - `-e`  Marks the user as erased. This means messages sent by
  the user will still be visible by anyone that was in the
  room when these messages were sent, but hidden from users
  joining the room afterwards.
  
  - `-h, --help`
  Show usage message.

<a id="user-details"></a>
#### details
```bash
synadmin user details [OPTIONS] USER_ID
```
  View details of a user account.

* Options
  - `-h, --help`  Show usage message.

<a id="user-list"></a>
#### list
```bash
synadmin user list [OPTIONS]
```
  List users, search for users.

* Options
  - `-f, --from INTEGER`          Offset user listing by given number. This
                                  option is also used for pagination.
  - `-l, --limit INTEGER`         Limit user listing to given number
  - `-d, --deactivated`           Show deactivated/erased users
  - `-a, --admins`                Whether to filter for admins, or non-admins.
                                  If not specified, no admin filter is
                                  applied.
  - `-n, --name TEXT`             Search users by name - filters to only
                                  return users with user ID localparts or
                                  displaynames that contain this value
  -  `-i, --user-id TEXT`         Search users by ID - filters to only return
                                  users with Matrix IDs (@user:server) that
                                  contain this value
  - `-h, --help`                  Show help message.

<a id="user-membership"></a>
#### membership
```bash
synadmin user membership [OPTIONS] USER_ID
```
  List all rooms a user is member of.

  Provide matrix user ID (@user:server) as argument.

* Options
  - `--aliases / --ids`  Display rooms as canonical aliases or room ID's.
                     [default: aliases]
  - `-h, --help`         Show help message.

<a id="user-modify"></a>
#### modify
```bash
synadmin user modify [OPTIONS] USER_ID
```
  Create or modify a local user. Provide matrix user ID (@user:server) as
  argument.

* Options
    - `-p, --password-prompt`         Set password interactively.
    - `-P, --password TEXT`           Set password on command line.
    - `-n, --display-name TEXT`       Set display name. defaults to the value of
                                      user_id
    - `-v, --avatar-url TEXT`         Set avatar URL. Must be a MXC URI (https://m
                                  atrix.org/docs/spec/client_server/r0.6.0#mat
                                  rix-content-mxc-uris)
    - `-a, --admin / -u  `            Grant user admin permission. Eg user is allowed to use the admin API.
    - `--activate`                    Re-activate user.
    - `--deactivate`                  Deactivate user.                      
    - `--user-type TEXT`              Change the type of the user. Currently
                                      understood by the Admin API are 'bot' and
                                      'support'. Use 'regular' to create a regular
                                      Matrix user.
    - `-l, --lock / -L, --unlock`     Whether to lock or unlock the account,
                                      preventing or allowing logins.
  - `-h, --help`                      Show help message.

 <a id="user-password"></a>
 #### password
 ```bash
 synadmin user password [OPTIONS] USER_ID
 ```
  Change a user's password.

  To prevent the user from being logged out of all sessions use option -n.

* Options
  - `-n, --no-logout`      Don't log user out of all sessions on all devices.
  - `-p, --password TEXT`  New password.
  - `-h, --help`           Show help message.

 <a id="user-search"></a>
 #### search
 ```bash
 synadmin user search [OPTIONS] SEARCH_TERM
 ```

  Searches for users by name/matrix-ID, including deactivated users as well as
  guest users. Also, compared to the original command, a case-insensitive
  search is done.

* Options
  - `-f, --from INTEGER`   Offset user listing by given number.
  - `-l, --limit INTEGER`  Maximum amount of users to return.
  - `-h, --help`           Show help message.

<a id="room"></a>
## Room
### Usage
```bash
synadmin room [OPTIONS] COMMAND [ARGS]...
```

  Manipulate rooms and room membership.

### Options
  `-h, --help`  Show help message.

### Room-Commands
  * [`block`](#room-block)          Block or unblock a room.
  * [`block-status`](#room-block-status)   Get if a room is blocked, and who blocked it.
  * [`delete`](#room-delete)        Delete and possibly purge a room.
  * [`delete-status`](#room-delete-status)  Get room deletion status via either the room ID or the...
  * [`details`](#room-details)        Get room details.
  * [`join`](#room-join)           Join a room.
  * [`list`](#room-list)           List and search for rooms.
  * [`make-admin`](#room-make-admin)     Grant a user room admin permission.
  * [`members`](#room-members)        List current room members.
  * [`search`](#room-search)         An alias to `synadmin room list -n <search-term>`.

<a id="room=block"></a>
#### block
```bash
synadmin room block [OPTIONS] ROOM_ID
```
  Block or unblock a room.

* Options
  - `-b, --block / -u, --unblock`  Specifies whether to block or unblock a room.
  - `-h, --help`                   Show this message and exit.

<a id="room-block-status"></a>
#### block-status
```bash
synadmin room block-status [OPTIONS] ROOM_ID
```
  Get if a room is blocked, and who blocked it.

<a id="room-delete"></a>
#### delete
```bash
synadmin room delete [OPTIONS] ROOM_ID
```
  Delete a room.

* Options
  - `-u, --new-room-user-id TEXT`  If set, a new room will be created with this
                                   user ID as the creator and admin, and all users
                                   in the old room will be moved into that room.
  - `-n, --room-name TEXT`         A string representing the name of the room that
                                   new users will be invited to.
  - `-m, --message TEXT`           A string containing the first message that will
                                   be sent as new_room_user_id in the new room.
  - `-b, --block`                  If set, this room will be added to a blocking
                                   list, preventing future attempts to join the
                                   room
  - `--no-purge`                   Prevent removing of all traces of the room from
                                   your database.
  - `--force-purge`                Force a purge to go ahead even if there are
                                   local users still in the room. 
  - `-h, --help`                   Show help message.

<a id="room-delete-status"></a>
#### delete-status
```bash
synadmin room delete-status [OPTIONS]
```
  Get room deletion status via either the room ID or the delete ID.

* Options
    - `-r, --room-id TEXT`            The Room ID to query the deletion status for
    - `-d, --delete-id TEXT`          The Delete ID
    - `-h, --help`                    Show help message.

<a id="room-details"></a>
#### details
```bash
synadmin room details [OPTIONS] ROOM_ID
```
  Get room details.

<a id="room-join"></a>
#### join
```bash
synadmin room join [OPTIONS] ROOM_ID_OR_ALIAS USER_ID
```
  Join a room.

<a id="room-list"></a>
#### list
```bash
synadmin room list [OPTIONS]
```
  List and search for rooms.

* Options
  - `-f, --from INTEGER`              Offset room listing by given number.
  - `-l, --limit INTEGER`             Maximum amount of rooms to return.
  - `-n, --name TEXT`                 Filter rooms by parts of their room name
  - `-s, --sort` [name|canonical_alias|joined_members|joined_local_members|version|creator|encryption|federatable|public|join_rules|guest_access|history_visibility|state_events]
                                      The method in which to sort the returned
                                      list of rooms.
  - `-r, --reverse`                   Direction of room order. If set it will
                                      reverse the sort order of --order-by method.
  - `-h, --help`                      Show help message.

<a id="room-make-admin"></a> 
#### make-admin
```bash
synadmin room make-admin [OPTIONS] ROOM_ID
```
  Grant a user room admin permission.

  If the user is not in the room, and it is not publicly joinable, then invite
  the user.

* Options
  - `-u, --user-id TEXT`  By default the server admin (the caller) is granted
                          power, but another user can optionally be specified.
  - `-h, --help`          Show help message.

<a id="room-members"></a>
#### members
```bash
synadmin room members [OPTIONS] ROOM_ID
```
  List current room members.

<a id="matrix"></a>
## Matrix
### Usage
```bash
synadmin matrix [OPTIONS] COMMAND [ARGS]...
```
  Execute Matrix API calls.

### Options
  `-h, --help`  Show help message.

### Matrix-Commands
  * `login`  Login to Matrix via username/password and receive an access token.
    ```bash
    synadmin matrix login [OPTIONS] USER_ID
    ```
    Login to Matrix via username/password and receive an access token.

    * Options
      - `-p, --password TEXT`  The Matrix user's password. If missing, an interactive
                           password prompt is shown.
      - `-h, --help`           Show help message.

<a id="notice"></a>
## Notice
### Usage
```bash
synadmin notice [OPTIONS] COMMAND [ARGS]...
```
  Send messages to users.

### Options
  `-h, --help`  Show help message.

### Commands
  * `send` server notices to users on the local homeserver.
  
    ```bash
    synadmin notice send [OPTIONS] TO PLAIN [FORMATTED]
    ```
    - TO
      Localpart or full matrix ID of the notice receiver. If --regex is set
      this will be interpreted as a regular expression.
    - PLAIN
      Plain text content of the notice.
    - FORMATTED
      Formatted content of the notice. If omitted, PLAIN will be used.
    
    * Options
      - `-f, --from-file`         Interpret arguments as file paths instead of
                                  notice content and read content from those
                                  files.
      - `-p, --batch-size SIZE`   The send command retrieves "pages" of users
                                  from the homeserver, filters them and sends
                                  out the notices, before retrieving the next
                                  page. SIZE sets how many users are in each
                                  of these "pages".
      - `-r, --regex `            Interpret TO as regular expression.
      - `-l,  LENGTH`             Length of the displayed list of matched
                                  recipients shown in the confirmation prompt.
      - `-h, --help`              Show this message and exit.

<a id="group"></a>
## Group
### Usage
```bash
synadmin group [OPTIONS] COMMAND [ARGS]...
```
  Manage groups (communities).

### Options
  `-h, --help`  Show help message.

### Commands
  * `delete` a local group (community).
  
    ```bash
    synadmin group delete [OPTIONS] GROUP_ID
    ```
