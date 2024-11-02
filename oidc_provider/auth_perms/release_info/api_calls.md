# Endpoints:

| Endpoint | Method | Description | Body parameters                                                                                              | View                                                                                                                                                                               |
| ------ | ------ | ------ |--------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| /about/|  ![#0000ff](https://via.placeholder.com/15/0000ff/000000?text=+) **GET** | Submodule Biom mode. Get page with json information about service and biom | <a name="GET /about/ back"></a>[Go to body parameters](#GET /about/)                                         | <a href=https://git.54origins.com/ecosystem54_protected/agpl/01_submodules_authsubmodule54/-/blob/5.10rc/core/auth_view.py#L59>AboutView</a>                                       |
| /actor/|  ![#ff0000](https://via.placeholder.com/15/ff0000/000000?text=+) **DELETE** | Delete actor based on request body, only for auth service | <a name="DELETE /actor/ back"></a>[Go to body parameters](#DELETE /actor/)                                   | <a href=https://git.54origins.com/ecosystem54_protected/agpl/01_submodules_authsubmodule54/-/blob/5.10rc/core/actor_view.py#L44>ActorView</a>                                      |
| /actor/|  ![#00FF00](https://via.placeholder.com/15/00FF00/000000?text=+) **POST** | Submodule Biom mode. Create actor based on request body, only for auth service | <a name="POST /actor/ back"></a>[Go to body parameters](#POST /actor/)                                       | <a href=https://git.54origins.com/ecosystem54_protected/agpl/01_submodules_authsubmodule54/-/blob/5.10rc/core/actor_view.py#L44>ActorView</a>                                      |
| /actor/|  ![#FFA500](https://via.placeholder.com/15/FFA500/000000?text=+) **PUT** | Submodule Biom mode. Update actor partially based on request body, only for auth service | <a name="PUT /actor/ back"></a>[Go to body parameters](#PUT /actor/)                                         | <a href=https://git.54origins.com/ecosystem54_protected/agpl/01_submodules_authsubmodule54/-/blob/5.10rc/core/actor_view.py#L44>ActorView</a>                                      |
| /actors/get|  ![#00FF00](https://via.placeholder.com/15/00FF00/000000?text=+) **POST** | Submodule Biom mode. Get actor by login value | <a name="POST /actors/get back"></a>[Go to body parameters](#POST /actors/get)                               | <a href=https://git.54origins.com/ecosystem54_protected/agpl/01_submodules_authsubmodule54/-/blob/5.10rc/core/actor_view.py#L172>GetActorByLoginValueView</a>                      |
| /apt54/|  ![#00FF00](https://via.placeholder.com/15/00FF00/000000?text=+) **POST** | Authentication with getting apt54 | <a name="POST /apt54/ back"></a>[Go to body parameters](#POST /apt54/)                                       | <a href=https://git.54origins.com/ecosystem54_protected/agpl/01_submodules_authsubmodule54/-/blob/5.10rc/core/auth_view.py#L907>APT54View</a>                                      |
| /auth/|  ![#00FF00](https://via.placeholder.com/15/00FF00/000000?text=+) **POST** | Authorization on client service | <a name="POST /auth/ back"></a>[Go to body parameters](#POST /auth/)                                         | <a href=https://git.54origins.com/ecosystem54_protected/agpl/01_submodules_authsubmodule54/-/blob/5.10rc/core/auth_view.py#L1063>ClientAuthView</a>                                |
| /auth_admin/|  ![#0000ff](https://via.placeholder.com/15/0000ff/000000?text=+) **GET** | Submodule Standalone. Redirect to page with profile info | <a name="GET /auth_admin/ back"></a>[Go to body parameters](#GET /auth_admin/)                               | <a href=https://git.54origins.com/ecosystem54_protected/agpl/01_submodules_authsubmodule54/-/blob/5.10rc/core/admin_view.py#L33>AdminView</a>                                      |
| /auth_admin/|  ![#00FF00](https://via.placeholder.com/15/00FF00/000000?text=+) **POST** | Submodule Standalone. Logout and redirect to home page | <a name="POST /auth_admin/ back"></a>[Go to body parameters](#POST /auth_admin/)                             | <a href=https://git.54origins.com/ecosystem54_protected/agpl/01_submodules_authsubmodule54/-/blob/5.10rc/core/admin_view.py#L33>AdminView</a>                                      |
| /auth_admin/actor/{uuid}/|  ![#0000ff](https://via.placeholder.com/15/0000ff/000000?text=+) **GET** | Submodule Standalone. Get page with actor detail based on uuid | <a name="GET /auth_admin/actor/{uuid}/ back"></a>[Go to body parameters](#GET /auth_admin/actor/{uuid}/)     | <a href=https://git.54origins.com/ecosystem54_protected/agpl/01_submodules_authsubmodule54/-/blob/5.10rc/core/admin_view.py#L171>AdminActorView</a>                                |
| /auth_admin/actor/{uuid}/|  ![#FFA500](https://via.placeholder.com/15/FFA500/000000?text=+) **PUT** | Submodule Standalone. Update an actor partially based on uuid and request body | <a name="PUT /auth_admin/actor/{uuid}/ back"></a>[Go to body parameters](#PUT /auth_admin/actor/{uuid}/)     | <a href=https://git.54origins.com/ecosystem54_protected/agpl/01_submodules_authsubmodule54/-/blob/5.10rc/core/admin_view.py#L171>AdminActorView</a>                                |
| /auth_admin/actors/|  ![#ff0000](https://via.placeholder.com/15/ff0000/000000?text=+) **DELETE** | Submodule Standalone. Delete actor based on request body | <a name="DELETE /auth_admin/actors/ back"></a>[Go to body parameters](#DELETE /auth_admin/actors/)           | <a href=https://git.54origins.com/ecosystem54_protected/agpl/01_submodules_authsubmodule54/-/blob/5.10rc/core/admin_view.py#L83>AdminActorsView</a>                                |
| /auth_admin/actors/|  ![#0000ff](https://via.placeholder.com/15/0000ff/000000?text=+) **GET** | Submodule Standalone. Get page with list of actors | <a name="GET /auth_admin/actors/ back"></a>[Go to body parameters](#GET /auth_admin/actors/)                 | <a href=https://git.54origins.com/ecosystem54_protected/agpl/01_submodules_authsubmodule54/-/blob/5.10rc/core/admin_view.py#L83>AdminActorsView</a>                                |
| /auth_admin/actors/|  ![#00FF00](https://via.placeholder.com/15/00FF00/000000?text=+) **POST** | Submodule Standalone. Create a new actor based on request body | <a name="POST /auth_admin/actors/ back"></a>[Go to body parameters](#POST /auth_admin/actors/)               | <a href=https://git.54origins.com/ecosystem54_protected/agpl/01_submodules_authsubmodule54/-/blob/5.10rc/core/admin_view.py#L83>AdminActorsView</a>                                |
| /auth_admin/permissions/|  ![#ff0000](https://via.placeholder.com/15/ff0000/000000?text=+) **DELETE** | Submodule Standalone. Delete permission | <a name="DELETE /auth_admin/permissions/ back"></a>[Go to body parameters](#DELETE /auth_admin/permissions/) | <a href=https://git.54origins.com/ecosystem54_protected/agpl/01_submodules_authsubmodule54/-/blob/5.10rc/core/admin_view.py#L300>AdminPermissionView</a>                           |
| /auth_admin/permissions/|  ![#00FF00](https://via.placeholder.com/15/00FF00/000000?text=+) **POST** | Submodule Standalone. Create permission | <a name="POST /auth_admin/permissions/ back"></a>[Go to body parameters](#POST /auth_admin/permissions/)     | <a href=https://git.54origins.com/ecosystem54_protected/agpl/01_submodules_authsubmodule54/-/blob/5.10rc/core/admin_view.py#L300>AdminPermissionView</a>                           |
| /auth_admin/permissions/|  ![#FFA500](https://via.placeholder.com/15/FFA500/000000?text=+) **PUT** | Submodule Standalone. Update permission | <a name="PUT /auth_admin/permissions/ back"></a>[Go to body parameters](#PUT /auth_admin/permissions/)       | <a href=https://git.54origins.com/ecosystem54_protected/agpl/01_submodules_authsubmodule54/-/blob/5.10rc/core/admin_view.py#L300>AdminPermissionView</a>                           |
| /auth_admin/profile/|  ![#0000ff](https://via.placeholder.com/15/0000ff/000000?text=+) **GET** | Submodule Standalone. Get page with self admin profile info | <a name="GET /auth_admin/profile/ back"></a>[Go to body parameters](#GET /auth_admin/profile/)               | <a href=https://git.54origins.com/ecosystem54_protected/agpl/01_submodules_authsubmodule54/-/blob/5.10rc/core/admin_view.py#L243>AdminProfileView</a>                              |
| /auth_admin/profile/|  ![#FFA500](https://via.placeholder.com/15/FFA500/000000?text=+) **PUT** | Submodule Standalone. Update self admin profile partially based on request body | <a name="PUT /auth_admin/profile/ back"></a>[Go to body parameters](#PUT /auth_admin/profile/)               | <a href=https://git.54origins.com/ecosystem54_protected/agpl/01_submodules_authsubmodule54/-/blob/5.10rc/core/admin_view.py#L243>AdminProfileView</a>                              |
| /auth_qr_code/|  ![#00FF00](https://via.placeholder.com/15/00FF00/000000?text=+) **POST** | Login with QR code | <a name="POST /auth_qr_code/ back"></a>[Go to body parameters](#POST /auth_qr_code/)                         | <a href=https://git.54origins.com/ecosystem54_protected/agpl/01_submodules_authsubmodule54/-/blob/5.10rc/core/auth_view.py#L2107>AuthQRCodeAuthorizationView</a>                   |
| /auth_sso_generation/|  ![#0000ff](https://via.placeholder.com/15/0000ff/000000?text=+) **GET** | Allow to authenticate with Auth session | <a name="GET /auth_sso_generation/ back"></a>[Go to body parameters](#GET /auth_sso_generation/)             | <a href=https://git.54origins.com/ecosystem54_protected/agpl/01_submodules_authsubmodule54/-/blob/5.10rc/core/auth_view.py#L114>AuthSSOGenerationView</a>                          |
| /auth_sso_generation/|  ![#00FF00](https://via.placeholder.com/15/00FF00/000000?text=+) **POST** | Session generation on service based on request body | <a name="POST /auth_sso_generation/ back"></a>[Go to body parameters](#POST /auth_sso_generation/)           | <a href=https://git.54origins.com/ecosystem54_protected/agpl/01_submodules_authsubmodule54/-/blob/5.10rc/core/auth_view.py#L114>AuthSSOGenerationView</a>                          |
| /auth_sso_login/|  ![#00FF00](https://via.placeholder.com/15/00FF00/000000?text=+) **POST** | Get session token after back redirect from auth single sign on | <a name="POST /auth_sso_login/ back"></a>[Go to body parameters](#POST /auth_sso_login/)                     | <a href=https://git.54origins.com/ecosystem54_protected/agpl/01_submodules_authsubmodule54/-/blob/5.10rc/core/auth_view.py#L2144>AuthSSOAuthorizationView</a>                      |
| /authorization/|  ![#0000ff](https://via.placeholder.com/15/0000ff/000000?text=+) **GET** | Submodule Biom mode. Get login template. If in SESSION TOKEN is SESSION, automatically adding js, css scripts from static folder. | <a name="GET /authorization/ back"></a>[Go to body parameters](#GET /authorization/)                         | <a href=https://git.54origins.com/ecosystem54_protected/agpl/01_submodules_authsubmodule54/-/blob/5.10rc/core/auth_view.py#L1699>AuthorizationView</a>                             |
| /get_invite_link_info/|  ![#00FF00](https://via.placeholder.com/15/00FF00/000000?text=+) **POST** | Info about create invite link | <a name="POST /get_invite_link_info/ back"></a>[Go to body parameters](#POST /get_invite_link_info/)         | <a href=https://git.54origins.com/ecosystem54_protected/agpl/01_submodules_authsubmodule54/-/blob/5.10rc/core/invite_link_view.py#L16>GetInviteLinkInfoView</a>                    |
| /get_qr_code/|  ![#0000ff](https://via.placeholder.com/15/0000ff/000000?text=+) **GET** | QR code generation | <a name="GET /get_qr_code/ back"></a>[Go to body parameters](#GET /get_qr_code/)                             | <a href=https://git.54origins.com/ecosystem54_protected/agpl/01_submodules_authsubmodule54/-/blob/5.10rc/core/auth_view.py#L237>GetQRCodeView</a>                                  |
| /get_session/|  ![#00FF00](https://via.placeholder.com/15/00FF00/000000?text=+) **POST** | Get session based on request body | <a name="POST /get_session/ back"></a>[Go to body parameters](#POST /get_session/)                           | <a href=https://git.54origins.com/ecosystem54_protected/agpl/01_submodules_authsubmodule54/-/blob/5.10rc/core/auth_view.py#L1647>GetSession</a>                                    |
| /masquerade/on/|  ![#00FF00](https://via.placeholder.com/15/00FF00/000000?text=+) **POST** | Use site as client | <a name="POST /masquerade/on/ back"></a>[Go to body parameters](#POST /masquerade/on/)                       | <a href=https://git.54origins.com/ecosystem54_protected/agpl/01_submodules_authsubmodule54/-/blob/5.10rc/core/masquerade_view.py#L11>MasqueradeOn</a>                              |
| /permaction/actor/|  ![#ff0000](https://via.placeholder.com/15/ff0000/000000?text=+) **DELETE** | Delete permactions for user | <a name="DELETE /permaction/actor/ back"></a>[Go to body parameters](#DELETE /permaction/actor/)             | <a href=https://git.54origins.com/ecosystem54_protected/agpl/01_submodules_authsubmodule54/-/blob/5.10rc/core/permaction_view.py#L24>ActorPermactionView</a>                       |
| /permaction/actor/|  ![#00FF00](https://via.placeholder.com/15/00FF00/000000?text=+) **POST** | Update permactions for user | <a name="POST /permaction/actor/ back"></a>[Go to body parameters](#POST /permaction/actor/)                 | <a href=https://git.54origins.com/ecosystem54_protected/agpl/01_submodules_authsubmodule54/-/blob/5.10rc/core/permaction_view.py#L24>ActorPermactionView</a>                       |
| /permaction/group/|  ![#ff0000](https://via.placeholder.com/15/ff0000/000000?text=+) **DELETE** | Delete permactions for group | <a name="DELETE /permaction/group/ back"></a>[Go to body parameters](#DELETE /permaction/group/)             | <a href=https://git.54origins.com/ecosystem54_protected/agpl/01_submodules_authsubmodule54/-/blob/5.10rc/core/permaction_view.py#L129>GroupPermactionView</a>                      |
| /permaction/group/|  ![#00FF00](https://via.placeholder.com/15/00FF00/000000?text=+) **POST** | Update permactions for group | <a name="POST /permaction/group/ back"></a>[Go to body parameters](#POST /permaction/group/)                 | <a href=https://git.54origins.com/ecosystem54_protected/agpl/01_submodules_authsubmodule54/-/blob/5.10rc/core/permaction_view.py#L129>GroupPermactionView</a>                      |
| /perms/|  ![#ff0000](https://via.placeholder.com/15/ff0000/000000?text=+) **DELETE** | Delete permissions from database that was sent from auth based on request body | <a name="DELETE /perms/ back"></a>[Go to body parameters](#DELETE /perms/)                                   | <a href=https://git.54origins.com/ecosystem54_protected/agpl/01_submodules_authsubmodule54/-/blob/5.10rc/core/permission_view.py#L37>PermissionView</a>                            |
| /perms/|  ![#00FF00](https://via.placeholder.com/15/00FF00/000000?text=+) **POST** | Create permissions in database that was sent from auth based on request body | <a name="POST /perms/ back"></a>[Go to body parameters](#POST /perms/)                                       | <a href=https://git.54origins.com/ecosystem54_protected/agpl/01_submodules_authsubmodule54/-/blob/5.10rc/core/permission_view.py#L37>PermissionView</a>                            |
| /reg/|  ![#00FF00](https://via.placeholder.com/15/00FF00/000000?text=+) **POST** | Registration with auth service | <a name="POST /reg/ back"></a>[Go to body parameters](#POST /reg/)                                           | <a href=https://git.54origins.com/ecosystem54_protected/agpl/01_submodules_authsubmodule54/-/blob/5.10rc/core/auth_view.py#L512>RegistrationView</a>                               |
| /save_session/|  ![#00FF00](https://via.placeholder.com/15/00FF00/000000?text=+) **POST** | Save session in cookies with flask session module based on request body | <a name="POST /save_session/ back"></a>[Go to body parameters](#POST /save_session/)                         | <a href=https://git.54origins.com/ecosystem54_protected/agpl/01_submodules_authsubmodule54/-/blob/5.10rc/core/auth_view.py#L1608>SaveSession</a>                                   |
| /synchronization/force/|  ![#00FF00](https://via.placeholder.com/15/00FF00/000000?text=+) **POST** | Force synchroniation | <a name="POST /synchronization/force/ back"></a>[Go to body parameters](#POST /synchronization/force/)       | <a href=https://git.54origins.com/ecosystem54_protected/agpl/01_submodules_authsubmodule54/-/blob/5.10rc/core/synchronization_view.py#L134>ProcessForcedSynchroniationDataView</a> |
| /synchronization/get_hash/|  ![#00FF00](https://via.placeholder.com/15/00FF00/000000?text=+) **POST** | Request on getting a actor, group, permaction hash | <a name="POST /synchronization/get_hash/ back"></a>[Go to body parameters](#POST /synchronization/get_hash/) | <a href=https://git.54origins.com/ecosystem54_protected/agpl/01_submodules_authsubmodule54/-/blob/5.10rc/core/synchronization_view.py#L17>GetSynchronizationHashView</a>               |


# Body parameters:


<a name="GET /about/"></a>
**GET /about/:**

[Return to endpoint](#GET /about/ back)
  * Request data:

```json
Content-Type: None
```
  * Response data:

```json
{
    "auth_biom_public_key": "04cdd9c94a9ecbc7fd4a0c2582a6e8b514edbc26d6281fabbc02cdbd01235772e81e6c179c8ceecfb39046972607a714267ca6cabafd69c2c21e41f76745e1364e",
    "biom_domain": "http://192.168.1.105:5000",
    "biom_name": null,
    "biom_uuid": "1ac09e56-3f09-4f02-83ff-028b2a41a398",
    "service_domain": "http://192.168.1.105:5002",
    "service_name": "Entity",
    "service_uuid": "db8972cd-c9e9-4cb9-9338-822209b71926"
}
```

<a name="DELETE /actor/"></a>
**DELETE /actor/:**

[Return to endpoint](#DELETE /actor/ back)
  * Request data:

```json
{
    "actor": {
        "uuid": "036ccf1b-8ad6-4240-8c08-d7914b90aa2c"
    },
    "service_uuid": "1ac09e56-3f09-4f02-83ff-028b2a41a398",
    "signature": "3045022100ac7c12bc09bccf93c5e290db29e5b56bd0609bb6eb899802aa88624e47e23b5002206bdb22c7881b00f04f54302cab80ce53bdb80d775c65a990c09735b1c5bb3454"
}
```
  * Response data:

```json
{
    "message": "Actor was successfully deleted."
}
```

<a name="POST /actor/"></a>
**POST /actor/:**

[Return to endpoint](#POST /actor/ back)
  * Request data:

```json
{
    "actor": {
        "uinfo": {
            "email": "test54@gmail.com",
            "login": "test54",
            "phone_number": "+111111111111",
            "groups": [
                "4c97a2dc-c0df-4af0-a5c7-1753c46ca2e1"
            ],
            "password": "ea82410c7a9991816b5eeeebe195e20a",
            "last_name": "test54",
            "first_name": "test54"
        },
        "actor_type": "classic_user"
    },
    "service_uuid": "1ac09e56-3f09-4f02-83ff-028b2a41a398",
    "signature": "30450220210c63db563853d0d5a7037fa67bdab930a9b578b759ccfcd2a7acb7549c255d022100e1cc6d1fc707e9dac3b5782bae4334d5306ec37123425bb0415c65957d8f0b60"
}
```
  * Response data:

```json
{
    "message": "Actor was successfully created."
}
```

<a name="PUT /actor/"></a>
**PUT /actor/:**

[Return to endpoint](#PUT /actor/ back)
  * Request data:

```json
{
    "actors": [
        {
            "uuid": "036ccf1b-8ad6-4240-8c08-d7914b90aa2c",
            "uinfo": {
                "email": "test54_new@gmail.com",
                "login": "test54_new",
                "phone_number": "+222222222222",
                "groups": [
                    "4c97a2dc-c0df-4af0-a5c7-1753c46ca2e1"
                ],
                "password": "ea82410c7a9991816b5ffffbe195e20a",
                "last_name": "test54_new",
                "first_name": "test54_new"
            },
            "actor_type": "classic_user"
        }
    ],
    "service_uuid": "1ac09e56-3f09-4f02-83ff-028b2a41a398",
    "signature": "30440220720ca2ca14307e5c9340b830bf862581b7fe421841ca09ccbc52b9d7741d9f30022048ee0757fd37390c360d0253884a66913adef985ea244e99942142d684b591a9"
}
```
  * Response data:

```json
{
    "message": "Actor was successfully updated."
}
```

<a name="POST /actors/get"></a>
**POST /actors/get:**

[Return to endpoint](#POST /actors/get back)
  * Request data:

```json
{
    "login_type": "email",
    "login_value": "test@gmail.com"
}
```
  * Response data:

```json
{
        "actor_type": "classic_user",
        "created": "2022-04-22 08:03:10.440056",
        "initial_key": None,
        "root_perms_signature": None,
        "secondary_keys": None,
        "total": 1,
            "uinfo": {
                "email": "test@gmail.com",
                "first_name": "test",
                "groups": ["4c97a2dc-c0df-4af0-a5c7-1753c46ca2e1"],
                "last_name": "test",
                "password": "098f6bcd4621d373cade4e832627b4f6"
                },
            "uuid": "22285f1d-12ab-4cc9-834c-5c0f5c75d9b9"
    }
```

<a name="POST /apt54/"></a>
**POST /apt54/:**

[Return to endpoint](#POST /apt54/ back)
  * Request data:

```json
{
    "step": 1,
    "uuid": "d573cb16-ebc6-47d2-80a2-d5bd76493881"
}
```
  * Response data:

```json
{
    "salt": "7b1dfead35b494b882e84c60ec13c570"
}
```

<a name="POST /auth/"></a>
**POST /auth/:**

[Return to endpoint](#POST /auth/ back)
  * Request data:

```json
{
    "email": "qwerty@gmail.com",
    "password": "qwerty",
    "actor_type": "classic_user"
}
```
  * Response data:

```json
{
    "apt54": "{\"expiration\": \"2022-05-13 08:50:57\", \"signature\": \"304402205f8770423cd21431c31a4746eaec849c6feb28d7a70746bf7616420359f1aa8d022015dc21d68831aaceb574377d816fd42b5fcbd8063f0beee040dfe7e59d0b4d55\", \"user_data\": {\"actor_type\": \"classic_user\", \"created\": \"2022-04-21 09:09:59\", \"initial_key\": \"04a35e8a437a54d4826e83c3c476201a5259a3933a07cc3c6e056b58de8f90802293c4b343a2e4ce789c951c9cb5ddf1cb59fdef76d8d96e0f5f2b1a8e617e6bf2\", \"root\": true, \"root_perms_signature\": \"30460221008241fd549d86047c709a18b43b6f1c1b67ba4c1192f2d6dce735cceb0af13d3a0221008483e430be2e81b1211d14b81c28ba1bf7974dd55cb707cc26a5bb0e5503cafd\", \"secondary_keys\": null, \"uinfo\": {\"email\": \"qwerty@gmail.com\", \"first_name\": \"qwerty_put\", \"groups\": [\"4c97a2dc-c0df-4af0-a5c7-1753c46ca2e1\"], \"last_name\": \"qwerty_pu\", \"password\": \"d8578edf8458ce06fbc5bb76a58c5ca4\"}, \"uuid\": \"66356f2e-987a-4031-af59-30a408f2fff5\"}}",
    "session_token": "7qvJT9E9p8DzcOhBQ3xhhs9O5fuAafpX"
}
```

<a name="GET /auth_admin/"></a>
**GET /auth_admin/:**

[Return to endpoint](#GET /auth_admin/ back)
  * Request data:

```json
Content-Type: None
```
  * Response data:

```json
Status Code: 200
    Content-Type: text/html; charset=utf-8
    Content-Length: 11862
    Access-Control-Allow-Origin: *
```

<a name="POST /auth_admin/"></a>
**POST /auth_admin/:**

[Return to endpoint](#POST /auth_admin/ back)
  * Request data:

```json
{}
```
  * Response data:

```json
Status Code: 200
    Content-Type: text/html; charset=utf-8
    Content-Length: 8488
    Access-Control-Allow-Origin: *
```

<a name="GET /auth_admin/actor/{uuid}/"></a>
**GET /auth_admin/actor/{uuid}/:**

[Return to endpoint](#GET /auth_admin/actor/{uuid}/ back)
  * Request data:

```json
Content-Type: None
```
  * Response data:

```json
Status Code: 200
    Content-Type: text/html; charset=utf-8
    Content-Length: 87652
    Access-Control-Allow-Origin: *
```

<a name="PUT /auth_admin/actor/{uuid}/"></a>
**PUT /auth_admin/actor/{uuid}/:**

[Return to endpoint](#PUT /auth_admin/actor/{uuid}/ back)
  * Request data:

```json
{
    "first_name": "test54_put",
    "last_name": "test54_put",
    "email": "test54_put@gmail.com",
    "birthday": null,
    "groups": [
        "dd909964-086c-4a81-8daf-34037c0bf544"
    ],
    "password": "ea82410c7a9991816b5eeeebe195e20a"
}
```
  * Response data:

```json
{
    "message": "Actor successfully updated"
}
```

<a name="DELETE /auth_admin/actors/"></a>
**DELETE /auth_admin/actors/:**

[Return to endpoint](#DELETE /auth_admin/actors/ back)
  * Request data:

```json
{
    "uuid": "d573cb16-ebc6-47d2-80a2-d5bd76493881"
}
```
  * Response data:

```json
{
    "message": "Actor was successfully deleted."
}
```

<a name="GET /auth_admin/actors/"></a>
**GET /auth_admin/actors/:**

[Return to endpoint](#GET /auth_admin/actors/ back)
  * Request data:

```json
Content-Type: None
```
  * Response data:

```json
Status Code: 200
    Content-Type: text/html; charset=utf-8
    Content-Length: 28951
    Access-Control-Allow-Origin: *
```

<a name="POST /auth_admin/actors/"></a>
**POST /auth_admin/actors/:**

[Return to endpoint](#POST /auth_admin/actors/ back)
  * Request data:

```json
{
    "uinfo": {
        "first_name": "test54",
        "last_name": "test54",
        "email": "test54@gmail.com",
        "login": "test54",
        "phone_number": "+111111111111",
        "password": "test54"
    },
    "actor_type": "classic_user"
}
```
  * Response data:

```json
{
    "message": "Actor was successfully created."
}
```

<a name="DELETE /auth_admin/permissions/"></a>
**DELETE /auth_admin/permissions/:**

[Return to endpoint](#DELETE /auth_admin/permissions/ back)
  * Request data:

```json
{
    "perm_uuid": "66eff516-5404-469a-8cb0-bb38d9e25912",
    "actor_uuid": "22285f1d-12ab-4cc9-834c-5c0f5c75d9b9"
}
```
  * Response data:

```json
{
    "message": "Success"
}
```

<a name="POST /auth_admin/permissions/"></a>
**POST /auth_admin/permissions/:**

[Return to endpoint](#POST /auth_admin/permissions/ back)
  * Request data:

```json
{
    "perm_uuid": "6d0bed92-c745-4113-a431-f0dfd6262174",
    "actor_uuid": "22285f1d-12ab-4cc9-834c-5c0f5c75d9b9",
    "value": 1,
    "params": {}
}
```
  * Response data:

```json
{
    "message": "Success"
}
```

<a name="PUT /auth_admin/permissions/"></a>
**PUT /auth_admin/permissions/:**

[Return to endpoint](#PUT /auth_admin/permissions/ back)
  * Request data:

```json
{
    "perm_uuid": "6d0bed92-c745-4113-a431-f0dfd6262174",
    "actor_uuid": "22285f1d-12ab-4cc9-834c-5c0f5c75d9b9",
    "value": 0,
    "params": {}
}
```
  * Response data:

```json
{
    "message": "Success"
}
```

<a name="GET /auth_admin/profile/"></a>
**GET /auth_admin/profile/:**

[Return to endpoint](#GET /auth_admin/profile/ back)
  * Request data:

```json
Content-Type: None
```
  * Response data:

```json
Status Code: 200
    Content-Type: text/html; charset=utf-8
    Content-Length: 11862
    Access-Control-Allow-Origin: *
```

<a name="PUT /auth_admin/profile/"></a>
**PUT /auth_admin/profile/:**

[Return to endpoint](#PUT /auth_admin/profile/ back)
  * Request data:

```json
{
    "first_name": "qwerty",
    "last_name": "qwerty",
    "email": "qwerty@gmail.com",
    "birthday": null,
    "password": "qwerty"
}
```
  * Response data:

```json
{
    "message": "Profile successfully updated"
}
```

<a name="POST /auth_qr_code/"></a>
**POST /auth_qr_code/:**

[Return to endpoint](#POST /auth_qr_code/ back)
  * Request data:

```json
Content-Type: application/x-www-form-urlencoded
    {"qr_token": "bAX4em9XaG5fivZMdj0CSD0MV2XgYLOV", "qr_type": "authentication"}:
```
  * Response data:

```json
{
    "session_token": "Ju4GMkL3vrjEAXVpAK38f3QBImlD8zQY"
}
```

<a name="GET /auth_sso_generation/"></a>
**GET /auth_sso_generation/:**

[Return to endpoint](#GET /auth_sso_generation/ back)
  * Request data:

```json
Content-Type: None
```
  * Response data:

```json
{
    "domain": "http://192.168.1.105:5000/auth_sso/",
    "service": "auth",
    "session": "Ng2YI6dovdBU5dgnFzfdlyvhN8e3Wh1m",
    "uuid": "1ac09e56-3f09-4f02-83ff-028b2a41a398"
}
```

<a name="POST /auth_sso_generation/"></a>
**POST /auth_sso_generation/:**

[Return to endpoint](#POST /auth_sso_generation/ back)
  * Request data:

```json
{
    "service_uuid": "1ac09e56-3f09-4f02-83ff-028b2a41a398",
    "apt54": {
        "signature": "30450220121503996c58fd118fd065fc4c638ba235f00ddee8446c514f3d1ff965408e8f022100898ffeb489f001ca4b4fe216c0e6d9ac321a271dd75a65d6aa8d3496cb89cc53",
        "user_data": {
            "root": true,
            "uuid": "66356f2e-987a-4031-af59-30a408f2fff5",
            "uinfo": {
                "email": "qwerty@gmail.com",
                "groups": [
                    "4c97a2dc-c0df-4af0-a5c7-1753c46ca2e1"
                ],
                "password": "d8578edf8458ce06fbc5bb76a58c5ca4",
                "last_name": "qwerty_pu",
                "first_name": "qwerty_put"
            },
            "created": "2022-04-21 09:09:59",
            "actor_type": "classic_user",
            "initial_key": "04a35e8a437a54d4826e83c3c476201a5259a3933a07cc3c6e056b58de8f90802293c4b343a2e4ce789c951c9cb5ddf1cb59fdef76d8d96e0f5f2b1a8e617e6bf2",
            "secondary_keys": null,
            "root_perms_signature": "30460221008241fd549d86047c709a18b43b6f1c1b67ba4c1192f2d6dce735cceb0af13d3a0221008483e430be2e81b1211d14b81c28ba1bf7974dd55cb707cc26a5bb0e5503cafd"
        },
        "expiration": "2022-05-06 14:56:11"
    },
    "temporary_session": "f2K71OqINJkdYWDxOmDP7AEG12qtxv8e",
    "signature": "304602210087beb04a22e8dc294fcd618df319e5a9a2932fd0d0e1b997ba3981d4fb15aa360221008803d47fc5e622f933397637e4dc7aaa847ae616311ee456413b7793b264c33b"
}
```
  * Response data:

```json
{
    "message": "Session token was successfully created."
}
```

<a name="POST /auth_sso_login/"></a>
**POST /auth_sso_login/:**

[Return to endpoint](#POST /auth_sso_login/ back)
  * Request data:

```json
Content-Type: application/x-www-form-urlencoded
    {"temporary_session": "f2K71OqINJkdYWDxOmDP7AEG12qtxv8e"}:
```
  * Response data:

```json
{
    "session_token": {
        "session_token": "VUHEI6Tdul9YCQ3fzHZEmhpByB3CZnMj"
    }
}
```

<a name="GET /authorization/"></a>
**GET /authorization/:**

[Return to endpoint](#GET /authorization/ back)
  * Request data:

```json
Content-Type: None
```
  * Response data:

```json
Status Code: 200
    Content-Type: text/html; charset=utf-8
    Content-Length: 125087
    Access-Control-Allow-Origin: *
    Vary: Cookie
```

<a name="POST /get_invite_link_info/"></a>
**POST /get_invite_link_info/:**

[Return to endpoint](#POST /get_invite_link_info/ back)
  * Request data:

```json
{
    "link_uuid": "68c27803-f8d4-4c8d-8dd5-3348f909f8f5",
    "service_uuid": "1ac09e56-3f09-4f02-83ff-028b2a41a398"
}
```
  * Response data:

```json
{
    "identifier": {
        "actor": "66356f2e-987a-4031-af59-30a408f2fff5",
        "created": "Thu, 21 Apr 2022 10:31:28 GMT",
        "group_uuid": "e81081ae-5c10-4b69-b787-89d0ae0a271e",
        "identifier": null,
        "link": null,
        "params": null,
        "uuid": "68c27803-f8d4-4c8d-8dd5-3348f909f8f5"
    }
}
```

<a name="GET /get_qr_code/"></a>
**GET /get_qr_code/:**

[Return to endpoint](#GET /get_qr_code/ back)
  * Request data:

```json
Content-Type: None
```
  * Response data:

```json
{
    "qr_code": "iVBORw0KGgoAAAANSUhEUgAAAhIAAAISAQAAAACxRhsSAAAEzklEQVR4nO2dX2rrOhDGv7kO5FGGLKBLUXZw19QldQf2UrKAgvVYUJj7oBlJbs9pD5xE5IZPD8VxlB82fIzmn1RR/O1Y//lrBEAGGWSQQQYZZJBBBhmNITYOkDOu5QrAVeScRIB0gP0BIOfk8883fg4yyPjNUFVVRFVV3abuj30fMhA1o0xZQoZNqT9bHuVdyHh+RnLruM4A0OR4OSrWeVJ9bQYUgJvcWz8HGWT8ESNuAJBE7HP4EMSLSzRuQLm693OQQcZPDJGXDCB8SDObumDS5qQOeQ4yyLDhsgsKIAFlyQeuEIRNJS6AAFMWhHdp8/rywKO8CxlPz1hFRGQG5JwOkHM6KuKlj/IRL8diT8VSAtU1eLB3IeMJGSXebwPApOakYioRfbkqk7cvv2C8T8b9GZaXKumnbVJdgqWfXKwAik79C+alyBjOqPnTjCLWIscmTEz+ESgSLXquYqVOybg/w1bxBb6oL+X2pKqa+yrAEnIJ+lU1249pT8kYw3AlboAt+UApQBWLuezn9Sa3avxR3oWM52XsdFqt6IK6xrs9BYL5B2ZPQ6Y9JWMUw+1kuWrBVJUjJu0dgqC6m0KdkjGC4VoL5nLaul/7UFrQHzV/dQ2oUzKGMtLR86fBSqaWA4BpV1/nXrv6KkeV882fgwwyfjWs2hT1WhtPAF3nTWUVQJGmDGDKQBIgXg4e64d30ds9BxlkfDtaXsrbTN01jc0/LeE/zCGo2QDGUWQMYtQ4ysKlsqiXsdUUv2ejuquaCKBOybg/o9pTL0CVvFTINcDPuypUzVCZoaVOyRjB6Oyp3WhirXNq/rSY3HqPOiVjEKOu8TA5Vg+0T/Gj9knD59GekjGcIeegXbO+LukAfRXfahpVVc6th6rtPL3xc5BBxh8wQrZ9fOtLhmk35NJFrXo5lC+8CfDKPmkyRjFqfb8t6i27v1vo4zZ1bgDjfTJGMrpteQoAnt0/ZSBsQHw7ZUGaAeAqus7vB5S0P64H5vnJGMTo7GnrNOn6+aMnUW2e9tkAxlFkDGLs8vy7gr7l9DHtGqS2vk+VOiVjEOOzf9ra9u2em1dtXadlBOZPyRjG+NzP7zET4DVS+9OaUD3AYn2fjGGMrv/U3NC2P6/eW6piY+1IYT8/GQMZfZ9065daWo20Oqnwxb+r/lOnZIxhdDtKu5t157MF/U3AdbVvgzol4+6MXR+KHzbhIVTuu1Nt/OLbR3kXMp6X0Z3C0wVTVYS+dd/7pRagGlX6p2QMY1g9aj0DQMgH217ydnQ3IJ2yAGLVqridMoCrAGkG61FkDGL05/ZYK389QWr7Wt9vg/aUjIGML+f11ZOmPAfgDkEtRXnbNP1TMoYxyrrvHXpTVqSTYv13UgGOKqUjBVOWuCjE+k/LPTevj/IuZDwvw/dFLwCQTuWTAIesxQ2tB1AgzbB+qZBhfuxyq+cgg4xvRwv1PSXlV81i2hY+1vfJeCDGpPr6koGoH1Jku758lB0ouqSjlVaXxHPPyRjG+GxPW7wP1NJ+rKXVuiWa50uRMZLx+f/xlXu1+2R3VF/um6vqDlXqlIz7MzzPX9bwCYhvMxAVAJIl+yVup+yL/HX3n3xu9hxkkPHdEP15zg9jfZR3IYMMMsgggwwyyCDj/8/4D0ve+3npfjH4AAAAAElFTkSuQmCC"
}
```

<a name="POST /get_session/"></a>
**POST /get_session/:**

[Return to endpoint](#POST /get_session/ back)
  * Request data:

```json
{
    "qr_token": "Wfkjwenk4ksjg6oo6",
    "temporary_session": "7h4s5kjI5CFU8KLD74TMc1QSVHWP8Sk0"
}
```
  * Response data:

```json
{
    "session_token": "XVKKdV86W8uHmdnAfQ1nWSxqbfECHpiQ"
}
```

<a name="POST /masquerade/on/"></a>
**POST /masquerade/on/:**

[Return to endpoint](#POST /masquerade/on/ back)
  * Request data:

```json
{
    "actor_uuid": "1b2eac61-d704-425b-8d7e-988a55ce2b94"
}
```
  * Response data:

```json
{
    "masquerade_session": "01sst9WdmirxHfwZwlrjJuEUJZy6FwJR",
    "primary_session": "so58Yi0V172Saf7MV0hIOT6BL9XUVuEs"
}
```

<a name="DELETE /permaction/actor/"></a>
**DELETE /permaction/actor/:**

[Return to endpoint](#DELETE /permaction/actor/ back)
  * Request data:

```json
{
    "permactions": [
        {
            "permaction_uuid": "5645021d-4f15-4b23-8a85-3b2ca16eb97e",
            "actor_uuid": "c08c2ab3-934a-412c-9e5a-fd8afa4475ae",
            "service_uuid": "1ac09e56-3f09-4f02-83ff-028b2a41a398"
        }
    ],
    "service_uuid": "1ac09e56-3f09-4f02-83ff-028b2a41a398",
    "signature": "304502201658630080ecdd14b4a2babe353983a5a2b7c145dad7d7589f1042eeae276ba7022100e03ffedc3080e9dcd5b040c24a414819884669a402fb3db279cac6a325417921"
}
```
  * Response data:

```json
{
    "message": "Permactions successfully updated."
}
```

<a name="POST /permaction/actor/"></a>
**POST /permaction/actor/:**

[Return to endpoint](#POST /permaction/actor/ back)
  * Request data:

```json
{
    "permactions": [
        {
            "permaction_uuid": "5645021d-4f15-4b23-8a85-3b2ca16eb97e",
            "actor_uuid": "c08c2ab3-934a-412c-9e5a-fd8afa4475ae",
            "service_uuid": "1ac09e56-3f09-4f02-83ff-028b2a41a398",
            "value": 1,
            "params": {}
        }
    ],
    "service_uuid": "1ac09e56-3f09-4f02-83ff-028b2a41a398",
    "signature": "3046022100e41c1ab2fd1b0efd177ca0ff6db9f900d4df634629a130e8479c6e413b543f1c022100d88c5e00ede4a29fca02a0d052124a26c7e6618dca147a4a6b8b37589aecc9da"
}
```
  * Response data:

```json
{
    "message": "Permactions successfully updated."
}
```

<a name="DELETE /permaction/group/"></a>
**DELETE /permaction/group/:**

[Return to endpoint](#DELETE /permaction/group/ back)
  * Request data:

```json
{
    "permactions": [
        {
            "permaction_uuid": "5645021d-4f15-4b23-8a85-3b2ca16eb97e",
            "actor_uuid": "cc2f6ce2-c473-4741-99f6-fd7aec45d073",
            "service_uuid": "1ac09e56-3f09-4f02-83ff-028b2a41a398"
        }
    ],
    "service_uuid": "1ac09e56-3f09-4f02-83ff-028b2a41a398",
    "signature": "3045022100cef111311d30d0d5333a58680cdcd68055e6f5696a622f189c43cc8c8eb0ebd3022069884c92452a3edbd01b101be6fb1a3670f7f9f8ab578d63b1854048f22de4d5"
}
```
  * Response data:

```json
{
    "message": "Permactions successfully updated."
}
```

<a name="POST /permaction/group/"></a>
**POST /permaction/group/:**

[Return to endpoint](#POST /permaction/group/ back)
  * Request data:

```json
{
    "permactions": [
        {
            "permaction_uuid": "5645021d-4f15-4b23-8a85-3b2ca16eb97e",
            "actor_uuid": "cc2f6ce2-c473-4741-99f6-fd7aec45d073",
            "service_uuid": "1ac09e56-3f09-4f02-83ff-028b2a41a398",
            "value": 1,
            "weight": 12,
            "params": {}
        }
    ],
    "service_uuid": "1ac09e56-3f09-4f02-83ff-028b2a41a398",
    "signature": "3045022100c2410cf523c70549cdcd7b3cfdf397cf027fac8bdfae71651aa5718e4e103a0f02202d4cd2e517de75c842d392c37efac33cd7f37ab21a93be8af616d746100323fd"
}
```
  * Response data:

```json
{
    "message": "Permactions successfully updated."
}
```

<a name="DELETE /perms/"></a>
**DELETE /perms/:**

[Return to endpoint](#DELETE /perms/ back)
  * Request data:

```json
{
    "permission": {
        "perm_id": "1ac09e56-3f09-4f02-83ff-028b2a41a398/CreateAttach/biom_perm001",
        "actor_id": "e2d866f3-17f0-49af-b6b1-a9403094ea1b"
    },
    "service_uuid": "1ac09e56-3f09-4f02-83ff-028b2a41a398",
    "signature": "3045022100e7d9a5bed9d12ced0a60d61ff79cb3a84e78e4bb2fcc16648a32128bdd7cacfc02203703fdfec84e4538472966d947ec1930c2070613c3c663da4964e5729b5b780f"
}
```
  * Response data:

```json
{
    "message": "Permission successfully deleted."
}
```

<a name="POST /perms/"></a>
**POST /perms/:**

[Return to endpoint](#POST /perms/ back)
  * Request data:

```json
{
    "actor": {
        "uuid": "e2d866f3-17f0-49af-b6b1-a9403094ea1b"
    },
    "permission": [
        {
            "perm_id": "1ac09e56-3f09-4f02-83ff-028b2a41a398/CreateAttach/biom_perm001",
            "uuid": "1f19f1bd-b0f6-405f-af75-7738593533fd",
            "perm_value": 1,
            "default_value": 0,
            "perm_type": "simple",
            "service_id": "1ac09e56-3f09-4f02-83ff-028b2a41a398",
            "actor_id": "e2d866f3-17f0-49af-b6b1-a9403094ea1b",
            "action_id": "1ac09e56-3f09-4f02-83ff-028b2a41a398/CreateAttach"
        }
    ],
    "service_uuid": "1ac09e56-3f09-4f02-83ff-028b2a41a398",
    "signature": "30460221008235c7fa361e9700ed8aafe8b9e9b0116c3e9b4152fce71e8360506e8be4216f022100b66f520cc175fa9ee3759318613ff16c33933bdc2b4bb59d2efd836de9d9f434"
}
```
  * Response data:

```json
{
    "message": "Permission successfully updated."
}
```

<a name="POST /reg/"></a>
**POST /reg/:**

[Return to endpoint](#POST /reg/ back)
  * Request data:

```json
{
    "uinfo": {
        "first_name": "test421",
        "last_name": "test421"
    },
    "email": "test421@gmail.com",
    "login": "test421",
    "phone_number": "+111111111112",
    "password": "test421",
    "password_confirmation": "test421",
    "actor_type": "classic_user"
}
```
  * Response data:

```json
{
    "user": {
        "actor_type": "classic_user",
        "created": "Fri, 29 Apr 2022 10:44:50 GMT",
        "initial_key": null,
        "root_perms_signature": null,
        "secondary_keys": null,
        "uinfo": {
            "email": "test421@gmail.com",
            "first_name": "test421",
            "groups": [
                "4c97a2dc-c0df-4af0-a5c7-1753c46ca2e1"
            ],
            "last_name": "test421",
            "login": "test421",
            "password": "6e8877bfa5e3c58f9de018d18ff823ef",
            "phone_number": "+111111111112"
        },
        "uuid": "7c71adbb-4cfe-4e91-b80e-9fcbc0de9812"
    }
}
```

<a name="POST /save_session/"></a>
**POST /save_session/:**

[Return to endpoint](#POST /save_session/ back)
  * Request data:

```json
{
    "session_token": "2dfTUcgbyj2GGIUc2RuanS8jkxGO6Qni"
}
```
  * Response data:

```json
{
    "message": "Session token successfully saved."
}
```

<a name="POST /synchronization/force/"></a>
**POST /synchronization/force/:**

[Return to endpoint](#POST /synchronization/force/ back)
  * Request data:

```json
{
    "service_uuid": "1ac09e56-3f09-4f02-83ff-028b2a41a398",
    "signature": "3045022100ea82fe54e5787b6a2722a84c7d0715975fdffa58762c711a157ad78244f979bd0220741d274a1389ced9036e724b42c532f7966a506ce4603b790ab00f44171f5f5d"
}
```
  * Response data:

```json
{
    "message": "Success."
}
```

<a name="POST /synchronization/get_hash/"></a>
**POST /synchronization/get_hash/:**

[Return to endpoint](#POST /synchronization/get_hash/ back)
  * Request data:

```json
{
    "service_uuid": "1ac09e56-3f09-4f02-83ff-028b2a41a398",
    "signature": "304402203f99c19cb807e87f3c9b1044c2a273adc8904a85a2686ec30d5e6c752b51dae1022014068244081d3baec473314b6ed06c73370a201f73f177d8e60699383c718bf6"
}
```
  * Response data:

```json
{
    "actor_hash": "6218863cb7100f8becfebca0f20aa679",
    "group_hash": "cfc885490054763a8cd554eee0c7fa9e",
    "permactions_hash_data": {
        "57aa1fd4-457d-433b-90a4-e573934efd7f": {
            "actor_permactions_hash": "0",
            "group_permactions_hash": "0"
        },
        "f05f50d6-1714-4124-bfc8-6093dd0892ef": {
            "actor_permactions_hash": "0",
            "group_permactions_hash": "0"
        }
    }
}
```
