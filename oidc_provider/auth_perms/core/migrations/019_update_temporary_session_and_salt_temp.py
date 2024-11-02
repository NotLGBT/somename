from . import base


class Migration(base.BaseMigration):
    """
    Add service_uuid for what session is created
    TODO: add index on salt?
    """

    forwards_query = f"""
        ALTER TABLE temporary_session DROP COLUMN IF EXISTS actor_sid;
        DO $$ BEGIN
            ALTER TABLE temporary_session ADD COLUMN actor_uuid UUID REFERENCES actor (uuid) ON DELETE CASCADE;
        EXCEPTION
            WHEN others THEN null;
        END $$;

        ALTER TABLE salt_temp DROP COLUMN IF EXISTS actor_sid;

        CREATE OR REPLACE FUNCTION delete_expired_temporary_sessions()
        RETURNS trigger AS
        $BODY$
        BEGIN
            DELETE FROM temporary_session WHERE created < (NOW() at time zone 'utc') - INTERVAL '1 day';
            RETURN NEW;
        END;
        $BODY$
        LANGUAGE plpgsql VOLATILE;

        DO $$ BEGIN
            IF NOT EXISTS(SELECT *
                FROM information_schema.triggers
                WHERE event_object_table = 'temporary_session'
                AND trigger_name = 'delete_expired_temporary_sessions_trigger'
            )
            THEN
                CREATE TRIGGER delete_expired_temporary_sessions_trigger AFTER INSERT ON temporary_session FOR EACH ROW
                EXECUTE PROCEDURE delete_expired_temporary_sessions();
            END IF;
        END $$;

        CREATE OR REPLACE FUNCTION delete_expired_salts()
        RETURNS trigger AS
        $BODY$
        BEGIN
            DELETE FROM salt_temp WHERE created < (NOW() at time zone 'utc') - INTERVAL '1 hour';
            RETURN NEW;
        END;
        $BODY$
        LANGUAGE plpgsql VOLATILE;

        DO $$ BEGIN
            IF NOT EXISTS(SELECT *
                FROM information_schema.triggers
                WHERE event_object_table = 'salt_temp'
                AND trigger_name = 'delete_expired_salts_trigger'
            )
            THEN
                CREATE TRIGGER delete_expired_salts_trigger AFTER INSERT ON salt_temp FOR EACH ROW
                EXECUTE PROCEDURE delete_expired_salts();
            END IF;
        END$$ ;
    """

    backwards_query = f"""
        DROP TRIGGER IF EXISTS delete_expired_salts_trigger ON salt_temp CASCADE;
        DROP TRIGGER IF EXISTS delete_expired_temporary_sessions_trigger ON temporary_session CASCADE;
    """