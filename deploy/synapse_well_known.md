# Homeserver well-known
For the correct operation of the Matrix Synapse server with the client application on the web server (e.g., nginx), paths with the corresponding responses need to be added.

## server

### path
`/.well-known/matrix/server`

### response
```json
{
    "m.server": "<host>"
}
```

## client

### path
`/.well-known/matrix/client`

### response
```json
{
    "m.homeserver": {
        "base_url": "https://<host>"
    }
}
```