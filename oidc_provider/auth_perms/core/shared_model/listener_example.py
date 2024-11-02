import json
import threading
from time import sleep
from abc import ABC
from abc import abstractmethod
from redis.exceptions import ConnectionError as RedisConnectionError

from .message_model import SharedMessage
from ..utils import logging_message


class BaseListener(ABC, threading.Thread):
    """"
    Base listener for redis
    """
    
    def  __init__(self, r, channels, app):
        threading.Thread.__init__(self)
        self.daemon = True
        self.redis = r
        self.pubsub = self.redis.pubsub()
        self.pubsub.subscribe(channels)
        self.app = app
        
    def work(self, item):
        with self.app.app_context():
            try:
                data = json.loads(item['data'])
                if data['type'] == 'SAVE':
                    self.save(data)
                elif data['type'] == 'CALLBACK':
                    self.callback(data)
            except ValueError as e:
                logging_message(f'Error decoding data: {str(e)}')
    
    @abstractmethod
    def save(self, data):
        raise NotImplementedError('Method should be implemented in child class')
    
    def callback(self, data):
        """ 
        Delete message
        Can be override if needed 
        """
        redis_message = SharedMessage.objects.get(id=data.get('message_id', ''))
        if redis_message:
            SharedMessage.objects.delete(redis_message.id)
        
    def run(self):
        while True:
            try:
                item = self.pubsub.get_message()
                if item and item['type'] == 'message':
                    self.work(item)
            except RedisConnectionError:
                logging_message('Redis is down')
                sleep(10)
            sleep(0.001)
