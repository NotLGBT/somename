from . import base


class Migration(base.BaseMigration):
    """
    Additional indexes on actor and service_session_token tables
    """
    forwards_query = f"""
    	CREATE INDEX IF NOT EXISTS btree_actor_email ON actor USING BTREE ((uinfo ->> 'email'));
    	CREATE INDEX IF NOT EXISTS btree_actor_login ON actor USING BTREE ((uinfo ->> 'login'));
        CREATE INDEX IF NOT EXISTS btree_actor_phone_number ON actor USING BTREE ((uinfo ->> 'phone_number'));

        CREATE INDEX IF NOT EXISTS btree_actor_first_name ON actor USING BTREE ((uinfo ->> 'first_name'));
        CREATE INDEX IF NOT EXISTS btree_actor_last_name ON actor USING BTREE ((uinfo ->> 'last_name'));
        CREATE INDEX IF NOT EXISTS btree_group_name ON actor USING BTREE ((uinfo ->> 'group_name'));
        CREATE INDEX IF NOT EXISTS btree_service_name ON actor USING BTREE ((uinfo ->> 'service_name'));
        CREATE INDEX IF NOT EXISTS btree_service_domain ON actor USING BTREE ((uinfo ->> 'service_domain'));
        CREATE INDEX IF NOT EXISTS btree_actor_full_name ON actor USING BTREE (((uinfo->>'first_name') || ' ' || (uinfo->>'last_name')));

        CREATE INDEX IF NOT EXISTS btree_actor_root_perms_signature ON actor (root_perms_signature);
        CREATE INDEX IF NOT EXISTS btree_actor_created_key ON actor (created);
        CREATE INDEX IF NOT EXISTS btree_actor_type_key ON actor (actor_type);

        CREATE INDEX IF NOT EXISTS gin_actor_groups ON actor USING GIN ((uinfo -> 'groups') jsonb_ops);

        CREATE INDEX IF NOT EXISTS btree_session_token_uuid_service_uuid ON service_session_token (uuid, service_uuid);
        CREATE INDEX IF NOT EXISTS btree_auxiliary_token ON service_session_token (auxiliary_token);
        """

    backwards_query = f"""
        DROP INDEX IF EXISTS btree_actor_email;
        DROP INDEX IF EXISTS btree_actor_login;
        DROP INDEX IF EXISTS btree_actor_phone_number;
        DROP INDEX IF EXISTS btree_actor_first_name;
        DROP INDEX IF EXISTS btree_actor_last_name;
        DROP INDEX IF EXISTS btree_group_name;
        DROP INDEX IF EXISTS btree_service_name;
        DROP INDEX IF EXISTS btree_service_domain;
        DROP INDEX IF EXISTS btree_actor_full_name;
        DROP INDEX IF EXISTS btree_actor_root_perms_signature;
        DROP INDEX IF EXISTS btree_actor_created_key;
        DROP INDEX IF EXISTS gin_actor_groups;
        DROP INDEX IF EXISTS btree_actor_type_key;
        DROP INDEX IF EXISTS btree_session_token_uuid_service_uuid;
        DROP INDEX IF EXISTS btree_auxiliary_token;
    """


    """
    NOTE: If your service has functionality to query actor table with huge number of rows (50000+)
    by LIKE/ILIKE operators in general (OR others which support only by trigams indexes),
    then connect to your database as superuser! and execute next queries to create gin_trgm_ops indexes

    CREATE EXTENSION IF NOT EXISTS pg_trgm;

    CREATE INDEX IF NOT EXISTS gin_trgm_actor_email ON actor USING GIN ((uinfo ->> 'email') gin_trgm_ops);
    CREATE INDEX IF NOT EXISTS gin_trgm_actor_login ON actor USING GIN ((uinfo ->> 'login') gin_trgm_ops);
    CREATE INDEX IF NOT EXISTS gin_trgm_actor_phone_number ON actor USING GIN ((uinfo ->> 'phone_number') gin_trgm_ops);
    CREATE INDEX IF NOT EXISTS gin_trgm_actor_first_name ON actor USING GIN ((uinfo ->> 'first_name') gin_trgm_ops);
    CREATE INDEX IF NOT EXISTS gin_trgm_actor_last_name ON actor USING GIN ((uinfo ->> 'last_name') gin_trgm_ops);
    CREATE INDEX IF NOT EXISTS gin_trgm_actor_group_name ON actor USING GIN ((uinfo ->> 'group_name') gin_trgm_ops);
    CREATE INDEX IF NOT EXISTS gin_trgm_actor_service_name ON actor USING GIN ((uinfo ->> 'service_name') gin_trgm_ops);
    CREATE INDEX IF NOT EXISTS gin_trgm_actor_full_name ON actor USING GIN (((uinfo->>'first_name') || ' ' || (uinfo->>'last_name')) gin_trgm_ops);
    """