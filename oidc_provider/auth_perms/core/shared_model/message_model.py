from ..exceptions import MultipleObjectsReturned

from ..managers import BaseManager
from ..utils import json_dumps
from ..utils import logging_message

from flask import current_app as app 


class MesssageManager(BaseManager):
    
    def get(self, **kwargs):
        """
        :return list of SharedMessage
        """
        if not kwargs:
            raise ValueError('No filter parameters provided')
        
        query, values = self.compile_query(**kwargs)
        with app.db.get_cursor() as cur:
            cur.execute(query, values)
            message = cur.fetchall()
        
        if not message:
            return []
        
        if len(message) > 1:
            raise MultipleObjectsReturned()
        else: 
            return SharedMessage(message[0])
        
    def all(self):
        query, values = self.compile_query()
        with app.db.get_cursor() as cur:
            cur.execute(query, values)
            messages = cur.fetchall()
            
        if not messages:
            return []
        
        return [SharedMessage(message) for message in messages]
        
    def order_by_id(self, desc=True):
        query = f"""SELECT * FROM shared__core_message ORDER BY id {'DESC' if desc else ''} """
        with app.db.get_cursor() as cur:
            cur.execute(query)
            messages = [SharedMessage(message) for message in cur.fetchall()]
        return messages
    
    def delete(self, id):
        query = """DELETE FROM shared__core_message WHERE id = %s """
        values = [id]
        with app.db.get_cursor() as cur:
            cur.execute(query, values)
            
    def save(self, channel, data):
        query = """INSERT INTO shared__core_message (channel, data)  VALUES(%s, %s::jsonb) RETURNING id"""
        values = [channel, json_dumps(data)]
        try: 
            with app.db.get_cursor() as cur:
                cur.execute(query, values)
                message_id = cur.fetchall()
        except Exception as e:
            logging_message(f"Error at creating message: {e}")
        return self.get(**message_id[0])
    
    def update(self, message_id, data):
        query = """UPDATE shared__core_message SET data = %s::jsonb WHERE id = %s::integer RETURNING id"""
        values = [json_dumps(data), message_id]
        try:
            with app.db.get_cursor() as cur:
                cur.execute(query, values)
                updated_message = cur.fetchall()
        except Exception as e:
            logging_message(f"Error on update message: {message_id} {e}")
            
        return self.get(**updated_message[0])
        
        
class SharedMessage:
    
    objects = MesssageManager(table_name='shared__core_message')
    
    def __init__(self, message):
        self.id = message.get('id')
        self.channel = message.get('channel')
        self.data = message.get('data')
        self.date_created = message.get('date_created')
    
    def __repr__(self) -> str:
        return f'Shared Message #{self.id}'
    
    @staticmethod
    def delete_all_test_message():
        query = """DELETE FROM shared__core_message WHERE data->>'is_test' = 'true'"""
        try:
            app.db.execute(query)
        except Exception as e:
            logging_message(e)
