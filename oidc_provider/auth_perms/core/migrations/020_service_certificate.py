from . import base


class Migration(base.BaseMigration):
    """
    Table for storing services self signed certificates.
    """

    table_name = "certificate"
    forwards_query = f"""
        CREATE TABLE {table_name} (
            id SERIAL PRIMARY KEY,
            certificate text,
            domain text,
            service_uuid uuid references actor(uuid) ON DELETE CASCADE,
            created timestamp DEFAULT (now() at time zone 'utc')
        );
    """

    backwards_query = f"""
        DROP TABLE {table_name}
    """