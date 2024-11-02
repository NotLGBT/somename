Project directories:  
oidc_provider: /home/oidc_provider


1. Create users, configure 'sudo' execution, create directories for logs

2. Install packages:
```bash
$ sudo apt update
$ sudo apt install vim git htop tmux unzip nginx python3-dev python3-venv redis-server build-essential libgmp-dev libgmp3-dev libssl-dev libffi-dev libpq-dev libxml2-dev libxslt1-dev -y
```

3. Install PostgreSQL 13: https://computingforgeeks.com/install-postgresql-on-debian-linux/


4. Run setup.sh script to create database, user, extensions and setup envirement.
```bash
bash ./setup.sh <username> <password> <database>
```
If the script worked for you, go to step 9


4. Create PostgreSQL databases, users and extensions:
   - For oidc_provider:
```bash
$ CREATE USER <username> WITH LOGIN ENCRYPTED PASSWORD '<password>'
$ CREATE DATABASE <database>;
$ GRANT ALL PRIVILEGES ON DATABASE <databse> TO <username>;
$ \c <database>
$ CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```
  
Note: extensions must be created in database from superuser


5. Generate oidc_provider keys:
```bash
$ mkdir -p OIDC_provider/keys
# generate private key
openssl genrsa -out OIDC_provider/keys/private.pem 2048
# generate public key
openssl rsa -in OIDC_provider/keys/private.pem -pubout -out OIDC_provider/keys/public.pem
```


6. In project directory create and activate venv:
```bash
$ python3 -m venv venv
$ source ./venv/bin/activate
```

7. Note: For some projects in venv must be added Gunicorn package (```bash$ pip3 install gunicorn```)


8. Install requirements for project:
```bash
$ pip3 install -r requirements.txt
```

9. Create and configure local_settings.py


10. Apply service and submodules migrations:
```bash
$ python3 manage.py migrate
```


11. Create service:
```bash
$ python3 namage.py create_service
```
save output in file local_settings.py


12. Create Record in service database about auth:
Record format:
```bash
$ INSERT INTO actor(uuid, initial_key, uinfo, actor_type) VALUES ('<AUTH_UUID>', '<AUTH_PUBLIC_KEY>', '{"biom_name": "<BIOM_NAME>", "service_name": "<AUTH_NAME>", "service_domain": "http(s)://<AUTH_DOMAIN>"}'::jsonb, 'service');
```  
Note: 'http://' or 'https://' required in domain record


13. Create database group records if not exists:
```bash
$ INSERT INTO actor(uuid, uinfo, actor_type) VALUES ('cc2f6ce2-c473-4741-99f6-fd7aec45d073', '{"weight": 4294967298, "group_name": "ADMIN"}'::jsonb, 'group');
$ INSERT INTO actor(uuid, uinfo, actor_type) VALUES ('dd909964-086c-4a81-8daf-34037c0bf544', '{"weight": 4294967299, "group_name": "BAN"}'::jsonb, 'group');
$ INSERT INTO actor(uuid, uinfo, actor_type) VALUES ('4c97a2dc-c0df-4af0-a5c7-1753c46ca2e1', '{"weight": 0, "group_name": "DEFAULT"}'::jsonb, 'group');
```

14. After configuring and starting, migrations:
```bash
$ python3 manage.py connect_biome
```

15. Create databse client record:
```bash
$ INSERT INTO oidc_client(client_id, client_secret, redirect_uri, scope) VALUES ('<CLIENT_ID>', '<CLIENT_SECRET>', '<REDIRECT_URI>', '<SCOPE>');
```
