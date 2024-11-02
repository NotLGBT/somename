# Auth Perms Submodule

The module implements the registration, authentication and issuance of permissions for users.

## 1. Release info

### 6.16rc

- [release naming info](release_info/release_naming.md)

## 2. Features

#### Added built-in logs functionalty

#### Changed receiving versions logic

#### Minor updates and improvements

## 3. Requirements

- [Python](https://www.python.org)~=3.9
- [Python requirements list](requirements.txt)
- [PostgreSQL](https://www.postgresql.org)>=9.6
- [PostgreSQL uuid-ossp](https://www.postgresql.org/docs/9.6/uuid-ossp.html)

## 4. License

- [License file](release_info/LICENSE)

## 5. Acceptance tests

- [Acceptance tests list](release_info/acceptancetests.md)

## 6. Documentation

- [API calls](release_info/api_calls.md)
- [Flows](docs_and_tests/flows.md)

## 7. Deploy

- Initialize local configuration file: `git submodule init`
- Fetch all data from repository: `git submodule update`
- Install requirements list: `pip install -r requirements.txt`
- Apply the migrations: `python manage.py migrate`
- Pass necessary data to local_settings.py
