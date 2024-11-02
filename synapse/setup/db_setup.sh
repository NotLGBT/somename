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
    sudo -u postgres psql -c "CREATE DATABASE $DATABASE_NAME WITH OWNER $USERNAME ENCODING 'UTF8' LC_COLLATE = 'C' LC_CTYPE = 'C' TEMPLATE template0;"
    echo "database '$DATABASE_NAME' created with owner '$USERNAME'."
fi