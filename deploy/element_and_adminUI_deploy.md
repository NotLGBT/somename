# Element-web

1. create config file for element-web container:
```bash
mkdir /opt/element-web
cd /opt/element-web
sudo vim /opt/element-web/config.json
```

2. paste settings
```json
{
    "default_server_config": {
        "m.homeserver": {
            "base_url": "<HOMESERVER_URL>",
            "server_name": "<SERVER_NAME>"
        },
        "m.identity_server": {
            "base_url": "http://vector.im"
        }
    },
    "disable_custom_urls": false,
    "disable_guests": false,
    "disable_login_language_selector": false,
    "disable_3pid_login": true,
    "brand": "Element",
    "integrations_ui_url": "http://scalar.vector.im/",
    "integrations_rest_url": "http://scalar.vector.im/api",
    "integrations_widgets_urls": [
        "http://scalar.vector.im/_matrix/integrations/v1",
        "http://scalar.vector.im/api",
        "http://scalar-staging.vector.im/_matrix/integrations/v1",
        "http://scalar-staging.vector.im/api",
        "http://scalar-staging.riot.im/scalar/api"
    ],
    "bug_report_endpoint_url": "http://element.io/bugreports/submit",
    "uisi_autorageshake_app": "element-auto-uisi",
    "default_country_code": "GB",
    "show_labs_settings": false,
    "features": {
    "m.login_type": true
    },
    "default_federate": false,
    "default_theme": "light",
    "room_directory": {
        "servers": ["<SERVER_NAME>"]
    },
    "enable_presence_by_hs_url": {
        "<HOMESERVER_URL>": true
    },
    "terms_and_conditions_links": [
        {
            "url": "http://element.io/privacy",
            "text": "Privacy Policy"
        },
        {
            "url": "http://element.io/cookie-policy",
            "text": "Cookie Policy"
        }
    ],
    "privacy_policy_url": "http://element.io/cookie-policy"
}
```

3. run docker container. example:
```bash
docker run -d --name element-web --restart always -p 127.0.0.1:8080:80 -v /opt/element-web/config.json:/app/config.json vectorim/element-web:latest
```

# Admin UI

1. clone git repo:
```bash
cd /opt
git clone https://github.com/Awesome-Technologies/synapse-admin.git
```

2. open docker-compose file:
```bash
vim /opt/synapse-admin/docker-compose.yml
```

3. edit settings:
`
version: "3"

services:
  synapse-admin:
    container_name: synapse-admin
    hostname: synapse-admin
    #image: awesometechnologies/synapse-admin:latest
    build:
     context: .

    # to use the docker-compose as standalone without a local repo clone,
    # replace the context definition with this:
    # context: https://github.com/Awesome-Technologies/synapse-admin.git

     args:
    # if you're building on an architecture other than amd64, make sure
    # to define a maximum ram for node. otherwise the build will fail.
    #   - NODE_OPTIONS="--max_old_space_size=1024"
    # default is .
    #   - PUBLIC_URL=/synapse-admin
    # You can use a fixed homeserver, so that the user can no longer
    # define it himself
       - REACT_APP_SERVER=https://<SERVER_NAME>
    ports:
      - "<PORT>:80"
    restart: unless-stopped
`