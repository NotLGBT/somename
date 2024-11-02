from . import base

class Migration(base.BaseMigration):
    """
    Create service_specific_admins table.
    """
    table_name = "service_specific_admins"
    forwards_query = f"""
        CREATE TABLE {table_name} (
            service_uuid uuid UNIQUE references actor(uuid) ON DELETE CASCADE,
            admins_data text[]
        );
        """

    backwards_query = f"""
        DROP TABLE {table_name} CASCADE
    """