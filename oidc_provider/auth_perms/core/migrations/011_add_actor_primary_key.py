from . import base


class Migration(base.BaseMigration):

    forwards_query = f"""
        DO $$ BEGIN
            ALTER TABLE actor ADD CONSTRAINT actor_pkey PRIMARY KEY ("uuid");
        EXCEPTION
            WHEN others THEN null;
        END $$;
        """

    backwards_query = f""""""
