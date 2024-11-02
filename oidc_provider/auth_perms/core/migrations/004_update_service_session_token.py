from . import base


class Migration(base.BaseMigration):
    """
    Update service_session table.
    """
    table_name = "service_session_token"
    forwards_query = f"""
        DO $$ BEGIN
        IF EXISTS(SELECT *
            FROM information_schema.columns
            WHERE table_name='{table_name}' and column_name='qr_token')
        THEN
            ALTER TABLE {table_name} RENAME COLUMN qr_token TO auxiliary_token;
        END IF;
        END $$;
        """

    backwards_query = f"""
    """
