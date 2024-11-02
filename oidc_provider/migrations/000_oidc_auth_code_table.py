from auth_perms.core.migrations import base


class Migration(base.BaseMigration):
    '''
    Create authorization code table.
    '''

    table_name = "oidc_auth_code"

    forwards_query = f"""
        CREATE TABLE {table_name} (
            auth_code character varying(32) UNIQUE,
            nonce character varying(32),
            client_id character varying(32) NOT NULL,
            redirect_uri character varying(255) NOT NULL,
            uuid uuid references actor(uuid) ON DELETE CASCADE,
            created timestamp DEFAULT NOW(),
            expiration timestamp DEFAULT (NOW() + INTERVAL '1 min')
        );
        """

    backwards_query = f"""
        DROP TABLE {table_name};
    """
