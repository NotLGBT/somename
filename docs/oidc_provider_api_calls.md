| Method | Endpoint | Description | usage | View |
| ------ | ------ | ------ | ------ | ------ |
| **GET** | /.well-known/openid-configuration | Provides metadata about the OpenID provider, such as available endpoints, supported algorithms and token schemes. | [Go to example](#GET /.well-known/openid-configuration) | DescriptiveView |
| **GET** | /.well-known/jwks/ | Provides a set of public keys used to verify a JSON Web Token (JWT) signature | [Go to example](#GET /.well-known/jwks) | JwksView |
| **GET** | /oidc/authorize | initializes the authentication process and redirects the user to the submodule authorization endpoint | [Go to example](#GET /oidc/authorize) | AuthorizationView |
| **GET** | /oidc/auth_code | Endpoint to obtain an authorization code after authorization, which can be exchanged for an access token. | [Go to example](#GET /oidc/callback) | AuthorizationCodeView |
| **POST** | /oidc/token | Exchanges the authorization code for an access token and an identification token. | [Go to example](#POST /oidc/token) | ActorView |


# Examples
<a name="GET /.well-known/openid-configuration"></a>
**GET /.well-known/openid-configuration**

  * Request:
```
GET https://example.com/.well-known/openid-configuration HTTP/1.1
    Host: example.com
    Accept: application/json
```
  * Response:
```json
{
  "issuer": "https://server.example.com",
  "authorization_endpoint": "https://server.example.com/oidc/authorize",
  "token_endpoint": "https://server.example.com/oidc/token",
  "jwks_uri": "https://server.example.com/.well-known/jwks",
  "response_types_supported": ["code"],
  "subject_types_supported": ["public"],
  "id_token_signing_alg_values_supported": ["RS256"],
  "scopes_supported": ["openid"]
}
```

<a name="GET /.well-known/jwks"></a>
**GET /.well-known/jwks**

  * Request:
```
GET /.well-known/jwks HTTP/1.1
    Host: example.com
    Accept: application/json
```

  * Response:
```json
{
  "keys": [
    {
      "kty": "RSA",
      "kid": "123456",
      "use": "sig",
      "n": "sXch9f0C8LkY_WU9wLk0M7q5k6P0gK8OBq...",
      "e": "AQAB"
    }
  ]
}
```

<a name="GET /oidc/authorize"></a>
**GET /oidc/authorize**

  * Request:
```
GET /oidc/authorize HTTP/1.1
    Host: server.example.com

    response_type=code
    &client_id=s6BhdRkqt3...
    &redirect_uri=https%3A%2F%2Fclient.example.org%2Fcb
    &scope=openid%20profile
    &state=af0ifejdw3u44ubf4k3rk34u4kn4edi3u2
    &nonce=dsjdsksefhe4hr3j4hgrj34htbjh
```

  * Response:
```
HTTP/1.1 302 Found
  Location: https://server.example.org/authorization/

  Set-Cookie: 
    client_id=s6BhdRkqt3...;
    redirect_uri=https%3A%2F%2Fclient.example.org%2Fcb;
    state=af0ifejdw3u44ubf4k3rk34u4kn4edi3u2;
    nonce=dsjdsksefhe4hr3j4hgrj34htbjh;
```

<a name="GET /oidc/auth_code"></a>
**GET /oidc/callback**

  * Request:
```
GET /oidc/callback HTTP/1.1
  
  Cookie:
    client_id=s6BhdRkqt3
    &redirect_uri=https%3A%2F%2Fclient.example.org%2Fcb
    &state=af0ifejdw3u44ubf4k3rk34u4kn4edi3u2
    &nonce=af0ifdddsjbdhsdedi3u2
```

  * Respose:
```
HTTP/1.1 302 Found
  Location: https://client.example.org/callback
    code=OEnefgfgfgdfdrgtrh55t45t45rgtfssdfjdksdj
    &state=af0ifejdw3u44ubf4k3rk34u4kn4edi3u2
```

<a name="POST /oidc/token"></a>
**POST /oidc/token**

  * Request:
```
POST /token HTTP/1.1
  Host: server.example.com
  Content-Type: application/x-www-form-urlencoded
  Authorization: Basic czZCaGRSa3F0MzpnWDFmQmF0M2JW

  grant_type=authorization_code
  &code=SplxlOBeZQQYbYS6WxSbIA
  &redirect_uri=https%3A%2F%2Fclient.example.org%2Fcb
```

  * Response:
```json
  {
   "id_token": "eyJhbrerfer3r4NIDJNr3vfdKvdIMzqg...",
   "access_token": "SlAV3d5jerferkjf34j3k...",
   "token_type": "Bearer",
   "expires_in": 3600
  }
```
