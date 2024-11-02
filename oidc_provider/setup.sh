#!/bin/bash

#SETUP DATABASE
# check params
if [ "$#" -ne 3 ]; then
    echo "usage: $0 <username> <password> <db_name>"
    exit 1
fi

USERNAME=$1
PASSWORD=$2
DATABASE_NAME=$3

# create user if not exists
EXISTING_USER=$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='$USERNAME';")
if [ "$EXISTING_USER" = "1" ]; then
    echo "user '$USERNAME' already exists."
else
    sudo -u postgres psql -c "CREATE ROLE $USERNAME WITH LOGIN ENCRYPTED PASSWORD '$PASSWORD';"
    echo "user '$USERNAME' created."
fi

# create database if not exists
EXISTING_DB=$(sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -w $DATABASE_NAME)
if [ -n "$EXISTING_DB" ]; then
    echo "database '$DATABASE_NAME' already exists."
else
    sudo -u postgres psql -c "CREATE DATABASE $DATABASE_NAME WITH OWNER $USERNAME;"
    sudo -u postgres psql -d $DATABASE_NAME -c 'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'
    echo "database '$DATABASE_NAME' created with owner '$USERNAME'."
fi

#---------------------------------------


#GENERATE PROVIDER KEYS
mkdir -p OIDC_provider/keys

# generate public key
openssl genrsa -out OIDC_provider/keys/private.pem 2048

# gnerate public key using private key
openssl rsa -in OIDC_provider/keys/private.pem -pubout -out OIDC_provider/keys/public.pem

echo "keys successfully generated"

#---------------------------------------


# VENV
python3.9 -m venv venv
source venv/bin/activate

pip install --upgrade pip


# install packages
pip install -r requirements.txt
pip install ../synapse_admin

# Деактивация виртуального окружения
deactivate