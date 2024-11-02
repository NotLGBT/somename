import json

from flask import current_app as app

from .decorator import fire_and_forget
from .message_model import SharedMessage

from ..ecdsa_lib import sign_data


class BaseSharedSaveModelsMixin:
    """
    Base Mixin for save, delta and push_to_redis/api functional
    """
    
    def save(self, shared_push: bool=False, channels_list: list=[], old_dict: dict={}, changed_classes_list: list=[], is_last: bool=False, is_test: bool=False, from_service: str=None):
        raise NotImplementedError('Method should be implemented in child class.') 
    
    def get_delta_data(self, old_dict: dict={}):
        raise NotImplementedError('Method should be implemented in child class.')
        
    def get_item_data(self):
        raise NotImplementedError('Method should be implemented in child class.')
    
    def push(self, data: dict, channel_list: list, client):
        """
        Method must be in save() method
        This method create Sharedmessages and send to service 
        Args:
            data (dict): data for sending 
            channel_list (list): list of channels/endpoints 
            client (_type_): Redis/API/etc client 
        """
        for channel in channel_list:
            message = SharedMessage.objects.save(channel, '')
            data['message_id'] = message.id
            message = SharedMessage.objects.update(message.id, data)
            if self.shared_type == 'REDIS':
                return self.push_to_redis(message.data, channel, client)
            elif self.shared_type == 'API':
                return self.push_to_api(message.data, channel, client)
        
        
    def push_to_redis(self, data: dict, channel: str, redis_client):
        """ 
        Called in method 'push'
        """
        redis_client.publish(channel, json.dumps(data))
    
    @fire_and_forget
    async def push_to_api(self, data: dict, service_url: str, client):
        """ 
        Called in method 'push' 
        Aslo waiting callback and delete SharedMessage by id 
        """
        service_uuid = app.config.get('SERVICE_UUID')
        data.update({'service_uuid': service_uuid})
        signature = sign_data(app.config.get('SERVICE_PRIVATE_KEY'), json.dumps(data))
        data.update({'signature': signature})
        response = await client.post(service_url, json=data)
        response_data = response.json()
        if response_data.get('type') == 'CALLBACK':
            message_id = response_data.get('message_id')
            if message := SharedMessage.objects.get(id=message_id):
                SharedMessage.objects.delete(message.id)

    
class BaseSharedDBModelsMixin:
    """
    Base Mixin for db methods 
    """
    
    @classmethod
    def get(cls, **kwargs):
        raise NotImplementedError('Method should be implemented in child class.')
    
    @classmethod
    def filter(cls, **kwargs):
        raise NotImplementedError('Method should be implemented in child class.')
    
    @classmethod
    def exclude(cls, **kwargs):
        raise NotImplementedError('Method should be implemented in child class.')
        
    @classmethod
    def update(cls, **kwargs):
        raise NotImplementedError('Method should be implemented in child class')
    
    @classmethod
    def get_or_create(cls, **kwargs):
        raise NotImplementedError('Method should be implemented in child class.') 

    @classmethod
    def all(cls):
        raise NotImplementedError('Method should be implemented in child class.') 

    @classmethod
    def order_by(cls, **kwargs):
        raise NotImplementedError('Method should be implemented in child class.') 

    @classmethod
    def exists(cls, **kwargs):
        raise NotImplementedError('Method should be implemented in child class.') 

    @classmethod
    def values(cls, **kwargs):
        raise NotImplementedError('Method should be implemented in child class.') 

    @classmethod
    def count(cls, **kwargs):
        raise NotImplementedError('Method should be implemented in child class.') 


class GeneralBaseMixin(
    BaseSharedDBModelsMixin, 
    BaseSharedSaveModelsMixin):
    pass
    