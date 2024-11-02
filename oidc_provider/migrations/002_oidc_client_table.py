from auth_perms.core.migrations import base


class Migration(base.BaseMigration):
    '''
    Create access token table.
    '''

    table_name = "oidc_client"

    forwards_query = f"""
        CREATE TABLE {table_name} (
            client_id character varying(32) UNIQUE,
            client_secret character varying(32) UNIQUE,
            redirect_uri character varying(255) NOT NULL,
            scope character varying(32) DEFAULT 'openid'
        );
        """
    
    backwards_query = f"""
        DROP TABLE {table_name};
    """