#CREATE ROOM
# check params
if [ "$#" -e 0 ]; then
    echo "Enter at least one room name"
    exit 1
fi

response=$(synadmin user logged-in)
status_code=$(echo "$response" | grep -o 'returned status code [0-9]*' | awk '{print $4}')
if [ "$status_code" -eq 401 ] || [ "$status_code" -eq 403 ]; then
       synadmin matrix login
fi

for room in "$@"; do
   synadmin room create-room "$room"
done