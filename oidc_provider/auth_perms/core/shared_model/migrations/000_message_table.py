from ...migrations.base import BaseMigration


class Migration(BaseMigration):
    """
    Create message table for shared models 
    """
    table_name = 'shared__core_message'
    forwards_query = f"""
    
            CREATE TABLE {table_name} (
                id SERIAL PRIMARY KEY,
                channel character varying(250),
                data jsonb,
                date_created timestamp DEFAULT (now() at time zone 'utc')
            );
        """

    backwards_query = f"""DROP TABLE {table_name} CASCADE"""
    