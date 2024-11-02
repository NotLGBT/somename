from . import base


class Migration(base.BaseMigration):

    forwards_query = f"""
        DO $$
        BEGIN
        IF EXISTS(SELECT *
            FROM information_schema.columns
            WHERE table_name='certificate' and column_name='domains')
        THEN
            ALTER TABLE certificate RENAME COLUMN domains TO domain;
        END IF;
        END $$;
    """

    backwards_query = f"""
    """