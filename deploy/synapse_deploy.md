Project directories:
synapse: /home/synapse

# Database setup

1. Create users

2. Install PostgreSQL 13: https://computingforgeeks.com/install-postgresql-on-debian-linux/

3. Run setup/db_setup.sh script to create database, user, extensions.
```bash
$ bash setup/db_setup.sh <username> <password> <database>
```
  If the script not worked for you, try:
```bash
$ sudo -u postgres bash

# this will prompt for a password for the new user
$ createuser --pwprompt <username>

$ createdb --encoding=UTF8 --locale=C --template=template0 --owner=<username> <database>
```

# Installing Synapse

**Installing as a Python module from PyPI**

1. To install the Synapse homeserver run:
```bash
$ python3 -m venv venv
$ source venv/bin/activate

$ pip install --upgrade pip
$ pip install --upgrade setuptools
$ pip install matrix-synapse
```

This Synapse installation can be upgraded by using pip again with the update flag:
```bash
$ pip install -U matrix-synapse
```

2. Before you can start Synapse, you will need to generate a configuration file. To do this, run:
```bash
$ python -m synapse.app.homeserver \
    --server-name your.domain.name \
    --config-path homeserver.yaml \
    --generate-config \
    --report-stats=[yes|no]
```

4. Configure homeserver. Look for example [here](config_samples/homeserver.yaml)


3. To run your homeserver:
```bash
synctl start
```

**Docker images**

1. Generating a configuration file:
```bash
$ docker run -it --rm \
    --mount type=volume,src=synapse-data,dst=/data \
    -e SYNAPSE_SERVER_NAME=my.matrix.host \
    -e SYNAPSE_REPORT_STATS=[yes|no] \
    matrixdotorg/synapse:latest generate
```

2. Running synapse:
```bash
$ docker run -d --name synapse \
    --mount type=volume,src=synapse-data,dst=/data \
    -p 8008:8008 \
    matrixdotorg/synapse:latest

```

# Well-Known URI's

Setting up the Well-Known URI's is optional but if you set it up, it will allow users to use clients which support well-known lookup to automatically configure the homeserver and identity server URLs.

The URL https://<server_name>/.well-known/matrix/client should return JSON in the following format:
```json
{
  "m.homeserver": {
    "base_url": "https://<matrix.example.com>"
  }
}
```

The URL https://<server_name>/.well-known/matrix/server should return JSON in format:
```json
{
    "m.server": "<matrix.example.com>"
}
```

# Setting up a TURN server

For video and audio calls you need to configure coturn:
```bash
$ sudo apt install coturn
```

Set the following settings in the file /etc/turnserver.conf:
```
listening-port=3478
fingerprint
use-auth-secret
static-auth-secret=Turn-Shared-Secret #Мы еге генерировали ранее во время настройки Matrix Synapse
realm=matrix.YOUR-DOMAIN.COM
# consider whether you want to limit the quota of relayed streams per user (or total) to avoid risk of DoS.
user-quota=100 # 4 streams per video call, so 100 streams = 25 simultaneous relayed calls per user.
total-quota=1200
no-tcp-relay # VoIP traffic is all UDP. There is no reason to let users connect to arbitrary TCP endpoints via the relay.
syslog
no-multicast-peers
```

# Create user with admin role
```bash
register_new_matrix_user -c homeserver.yaml
```