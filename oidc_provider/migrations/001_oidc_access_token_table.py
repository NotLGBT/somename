from auth_perms.core.migrations import base


class Migration(base.BaseMigration):
    '''
    Create access token table.
    '''

    table_name = "oidc_access_token"

    forwards_query = f"""
        CREATE TABLE {table_name} (
            access_token character varying(255) UNIQUE,
            uuid uuid references actor(uuid) ON DELETE CASCADE,
            created timestamp DEFAULT (now() at time zone 'utc'),
            expiration timestamp DEFAULT (now() at time zone 'utc'),
            token_type character varying(64) DEFAULT 'bearer'
        );
        """
    
    backwards_query = f"""
        DROP TABLE {table_name};
    """