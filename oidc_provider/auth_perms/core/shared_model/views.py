from flask import Response, make_response, jsonify
from flask import current_app as app 
from flask.views import MethodView
from flask_cors import cross_origin

from ..decorators import admin_only
from ..decorators import service_only
from ..decorators import data_parsing

from .decorator import shared_only
from .load_test import BaseLoadGeneralUtils
from .utils import SharedModelsDocumentationBuilder


class BaseLoadTestView(BaseLoadGeneralUtils, MethodView):
    """
    Base view for load test
    """
    methods = ['POST']
    redis_client = None
    model_class = None 
    
    @service_only
    @admin_only
    @cross_origin()
    @data_parsing
    def post(self, data) -> Response: 
        if not self.model_class:
            raise NotImplementedError('You must define model_class to use this view.')
        action = data.get('action')
        type = data.get('type')
        checksum = data.get('checksum')
        entities = data.get('entities')
        result = {}
        if all([action == 'check', entities]) or all([action == 'collect', type in ('creation', 'full', 'delta'), checksum]) or action == 'delete':
            #check if service is avaiable and listen a correct redis 
            if action == 'check':
                if self.model_class.shared_type == 'REDIS':
                    if not self.redis_client:
                        raise NotImplementedError('You must define redis_client to use this view.')
                    redis_channels = [channel.decode('utf-8') for channel in self.redis_client.pubsub_channels()]
                    if app.config.get('SERVICE_CHANNEL') in redis_channels:
                        result = {
                            'is_available': True,
                            'channel': app.config.get('SERVICE_CHANNEL')
                        }
                    else: 
                        result = {
                            'is_available': False,
                            'description': 'Check Redis channel'
                        } 
                else:
                    
                    result = {
                        'is_available': True,
                        'domain': app.config.get('SERVICE_DOMAIN')
                    }
                    
            #get checksum from service         
            elif action == 'collect':
                try:
                    local_checksum = self.get_checksum() 
                    result = {
                        'checksums_equals': checksum == local_checksum,
                    }
                    if self.redis_client and self.model_class.shared_type == 'REDIS':
                        result.update({'channel': app.config.get('SERVICE_CHANNEL')})
                    else:
                        result.update({'channel': app.config.get('SERVICE_DOMAIN')})
                except SystemError as e:
                    return make_response(jsonify(f'Exception while calculating checksum: {e.text}'), 400)
            #after finish test delete all test data from service
            else:
                success = self.delete_test_data()
                if success:
                    result.update({'success': True})
                else:
                    return make_response(jsonify(f'Exception during data deletion'), 400)
                
        else:
            return make_response(jsonify('Unknown action or checksum not delivered'), 400)
        return make_response(jsonify(result), 200)
    

class BaseSharedModelsAPIView(MethodView):
    """
    Base view for api usage
    """
    methods = ['POST']
    model_class = None
        
    def save(self, **kwargs) -> Response:
        """
        Main method to get data from reqeust 
        """
        raise NotImplementedError('Method should be implemented in child class')
    
    @shared_only
    @cross_origin()
    @data_parsing
    def post(self, data):
        if not self.model_class:
            raise NotImplementedError('You must define model_class to use this view.')
        if data.get('type') == 'SAVE':
            response = self.save(data)
        else:
            response = jsonify({'error': 'wrong type'})
        return response
    
  
class SharedModelsDocumentationView(MethodView):
    
    methods = ['POST']

    @service_only
    @admin_only
    @cross_origin()
    def post(self):
        shared_models_builder = SharedModelsDocumentationBuilder()
        shared_models_builder.create_shared_models_documentation(app)
        result = {
            'documentation': shared_models_builder.json_doc
        }
        return make_response(jsonify(result), 200)
    