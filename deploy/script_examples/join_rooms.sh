#!/bin/bash

if [ "$#" -le 2 ]; then
    echo "Enter '<user_id>' and at least one <room_id>"
    exit 1
fi

user=$1
rooms="${@:2}"

response=$(synadmin user logged-in)
status_code=$(echo "$response" | grep -o 'returned status code [0-9]*' | awk '{print $4}')
if [ "$status_code" -eq 401 ] || [ "$status_code" -eq 403 ]; then
       synadmin matrix login
fi

for room in "$rooms"; do
    synadmin room join-rooms "$rooms" "$user"
done