#TODO general refactor ABC 
import json
import random 
import string 
import datetime

from flask import current_app as app 

from ..exceptions import ServiceRequestError
from ..service_view import BaseServiceCommunication
from .message_model import SharedMessage


class BaseLoadGeneralUtils:
    
    def get_checksum(self):
        raise NotImplementedError('Method should be implemented in child class.')

    
    def delete_test_data(self):
        raise NotImplementedError('Method should be implemented in child class.')
    

class BaseCommandLoadTestUtils:
    """
    Base class for load test 
    """
    model = None 

    def create_delta(self, object, lists):
        raise NotImplementedError('Method should be implemented in child class.') 
    
    def create_test_data(self, **kwargs):
        raise NotImplementedError('Method should be implemented in child class.')
    
    @staticmethod
    def delete_message():
        """
        Delete message from database 
        """
        SharedMessage.delete_all_test_message()
        
        
    def get_value_for_field(self, entity, field):
        """
        Prepare turple with attributes name and type of them and generate random data 
        """
        raise NotImplementedError('Method should be implemented in child class.')
    
    def change_and_save_entity(self, **kwargs):
        raise NotImplementedError('Methdo should be implemented in child class.')
    
    @staticmethod
    def get_random_string(length=16):
        return ''.join(random.choice(string.ascii_letters) for i in range(length)) if length > 0 else ''

    def get_random_dict(self):
        return {self.get_random_string(): self.get_random_string() for i in range(random.randrange(2, 5))}

    @staticmethod
    def get_approximate_end_time(waiting_time):
        return (datetime.datetime.now() + datetime.timedelta(0, waiting_time)).strftime("%m/%d/%Y at %H:%M:%S")
    
    
class BaseLoadTestMainMethods(BaseCommandLoadTestUtils, BaseLoadGeneralUtils):

    
    def __init__(self, receivers=None, entities=None, type=None, fields=None, command=None, run_by=None, test_uuid=None, model=None):
        self.receivers = receivers
        self.entities = entities
        self.type = type 
        self.fields = fields
        self.command = command
        self.run_by = run_by
        self.test_uuid = test_uuid 
        self.apidoc_model = model
        
    def test_creation_functionality(self):
        raise NotImplementedError('Method should be implemented in child class.')
    
    def test_full_functionality(self):
        raise NotImplementedError('Method should be implemented in child class.')
    
    def test_delta_functionality(self):
        raise NotImplementedError('Method should be implemented in child class.')
    
    def save_load_testing_result(self, *kwargs):
        raise NotImplementedError('Method should be implemented in child class.')

    def _wait_creation_objects(self, result):
        """_
        Wait after creation objects while status not change to patrilly-finish and compare checksum
        """
        services = {}
        next_step = self.receivers.copy()
        while True:
            result_load_test_query = """SELECT * FROM load_testing_results WHERE status = 'partially-finish';"""
            
           
            result_load_test = app.db.fetchone(result_load_test_query)
            
            if result_load_test and result_load_test.get('status') == 'partially-finish':                 
                start_time_checksum_creation = datetime.datetime.now()
                for service in self.receivers:
                    
                    data = TriggerServiceForLoadTestingView(service, 'collect', self.type, result.get('checksum')).execute()
            
                    if data.get('checksums_equals') == False:
                        services[service.uinfo.get('service_name')] = {
                            'service_name': service.uinfo.get('service_name'),
                            'domain': service.uinfo.get('service_domain'),
                            'channel': data.pop('channel'),
                            'checksums_equals': data.get('checksums_equals', False)
                        }
                        next_step.remove(service)
                    else:
                        services[service.uinfo.get('service_name')] = {
                            'service_name': service.uinfo.get('service_name'),
                            'domain': service.uinfo.get('service_domain'),
                            'channel': data.pop('channel'),
                            'checksums_equals': data.get('checksums_equals')
                        }
                self.spend_time_checksum = datetime.datetime.now() - start_time_checksum_creation
                break
        return services, next_step
    

class TriggerServiceForLoadTestingView(BaseServiceCommunication):
    """ 
    Class with communicate /load_testing/ endpoint in service  
    """

    def __init__(self, service=None, action=None, type=None, checksum=None, entities=None):
        super().__init__(service)
        self.method = 'post'
        self.endpoint = '/load_testing/'
        self.action = action
        self.type = type
        self.checksum = checksum
        self.entities = entities

    def execute(self):
        try:
            response = self.send_request(
                data={
                    'service_uuid': self.service.uuid,
                    'action': self.action,
                    'type': self.type,
                    'checksum': self.checksum,
                    'entities': self.entities
                },
                is_signed=False,
                timeout=60
            )

        except ServiceRequestError as e:
            return {
                'error': f'Service {self.service.uinfo["service_name"]} is down', 
            }
        if not response.ok:
            if self.type == 'check':
                return {
                    'error':f"Service {self.service.uinfo['service_name']} with UUID {self.service.uuid} in unavailable\n"
                }
            return {
            'status_code': response.status_code,
            'description': response.text
        } 
        return json.loads(response.content)
