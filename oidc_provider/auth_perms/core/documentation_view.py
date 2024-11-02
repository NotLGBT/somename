import re
import os
import json
import ast
import inspect
from flask import current_app as app
from flask import jsonify
from flask import make_response
from flask.views import MethodView
from flask_cors import cross_origin

from .utils import ssh_to_https
from .decorators import service_only
from .decorators import admin_only


class ApiCallsBuilder:

    def __init__(self):
        self.cls = None
        self.app = None
        self.views = set()
        self.app_endpoints = dict()
        self.endpoint_note = "endpoint"
        self.request_body_note = "body_request"
        self.response_body_note = "body_response"
        self._submodules = None
        self._submodules_info = None
        self.json_doc = dict()

    def get_all_views_from_app(self):
        return [
            f.view_class
            for k, f in self.app.view_functions.items()
            if hasattr(f, "view_class")
        ]

    def sort(self):
        self.views = sorted(
            self.views,
            key=lambda cls: self.app_endpoints.get(cls)
                            or self.find_description(self.endpoint_note, cls.__doc__),
        )

    def find_app_endpoints(self):
        for rule in self.app.url_map.iter_rules():
            cls = self.app.view_functions.get(rule.endpoint)
            if hasattr(cls, "view_class"):
                endpoint = str(rule).replace("<", "{").replace(">", "}")
                endpoint = endpoint.replace("//", "/")
                self.app_endpoints[cls.view_class] = endpoint

    def get_app_or_view_cls(self):
        if hasattr(self.cls, "app_context") and hasattr(self.cls, "url_map"):
            self.app = self.cls
        else:
            raise ValueError(f'Argument must be Flask application object, not {self.cls}')

    def get_endpoint(self, cls):
        docstring = cls.__doc__ or ""
        return self.app_endpoints.get(cls) or self.find_description(self.endpoint_note, docstring)

    def create_body_param_doc(self, method, endpoint, docstring):
        request_keyword = f"{method}_{self.request_body_note}"
        response_keyword = f"{method}_{self.response_body_note}"
        request_body = self.find_description(request_keyword, docstring)
        response_body = self.find_description(response_keyword, docstring)
        format_request_body = self.is_json(request_body)
        format_response_body = self.is_json(response_body)
        self.json_doc[endpoint]['methods'][method]['body_params'] = dict()
        self.json_doc[endpoint]['methods'][method]['body_params']['request_body'] = format_request_body
        self.json_doc[endpoint]['methods'][method]['body_params']['response_body'] = format_response_body

    def create_doc_with_table(self, cls):
        endpoint = self.get_endpoint(cls).replace("|", "¦")
        filepath = inspect.getfile(cls)
        self.json_doc[endpoint] = {
            'methods': dict(),
            'view_func': cls.__name__,
            'submodule': self.get_submodule_name_by_path(filepath)
        }
        for method in sorted(cls.methods):
            self.json_doc[endpoint]['methods'][method] = dict()
            self.create_body_param_doc(method, endpoint, cls.__doc__)

            description = self.find_description(method, cls.__doc__).replace("\n", "")
            self.json_doc[endpoint]['methods'][method]['description'] = description

            local_path = os.getcwd()
            path_to_view = str(cls).replace('.', '/').replace("<class '", '').replace('>', '').split('/')[:-1]
            b = ''
            c = 0
            for i in path_to_view:
                if len(path_to_view) - c == 1:
                    b += i + '.py'
                else:
                    b += i + '/'
                c += 1
            if b.split('/')[0] == local_path.split('/')[-1]:
                local_path = local_path.replace(b.split('/')[0], '')
            class_line = inspect.getsourcelines(cls)
            git_link = self.create_git_file_link(os.path.join(local_path, b))
            git_link += f'#L{class_line[-1]}'
            self.json_doc[endpoint]['methods'][method]['git_link'] = git_link

    def get_current_repository_link(self, file=None):
        file = file or os.getcwd()
        from pygit2 import Repository
        repo = Repository(file)
        branch = repo.head.name.split('heads/')[-1]
        remote_url = repo.remotes['origin'].url
        # Check if remote url is ssh
        remote_url = ssh_to_https(remote_url)
        return f'{remote_url}/-/blob/{branch}'

    def create_git_file_link(self, filename):
        root = os.getcwd()

        if not str(filename).startswith(root):
            repo = self.get_current_repository_link(filename)
            i = filename.find('/')
            if i >= 0:
                filename = filename[i:]
            link = repo + filename
        else:
            submodules = self.get_submodules()

            for subm in submodules:
                if filename.startswith(subm['path']):
                    link = subm['https_url'] + '/-/tree/' + subm['last_commit'] + filename.replace(subm['path'], '')
                    break
            else:      
                for subm in self.submodules:
                    if subm.split('/')[0] in root:
                        root = root.replace(subm.split('/')[0] + '/', '')
                current_repository_link = self.get_current_repository_link()
                link = current_repository_link + '/' + filename.replace(root, '')
        return link

    def get_submodules(self):
        result = []
        root = os.getcwd()
        for subm in self.submodules:
            if (split_part:=subm.split('/')[0]) in root:
                if subm.endswith('/'):
                    split_part += '/'
                root = root.replace(split_part, '')
            abs_path = os.path.join(root, subm)
            from pygit2 import Repository
            subm_repo = Repository(abs_path)
            result.append({
                'https_url': ssh_to_https(subm_repo.remotes['origin'].url),
                'path': abs_path,
                'last_commit': str(subm_repo.head.target)
            })
        return result
    
    @property
    def submodules(self):
        if self._submodules is None:
            root = os.getcwd()
            from pygit2 import Repository
            repo = Repository(root)
            self._submodules = repo.listall_submodules()
        return self._submodules
    
    @property
    def submodules_info(self):
        if self._submodules_info is None:
            result = []
            root = os.getcwd()
            from pygit2 import Repository
            repo = Repository(root)
            for subm in self.submodules:
                if (split_part:=subm.split('/')[0]) in root:
                    if subm.endswith('/'):
                        split_part += '/'
                    root = root.replace(split_part, '')
                abs_path = os.path.join(root, subm)
                subm_repo = Repository(abs_path)
                result.append({
                    'https_url': ssh_to_https(subm_repo.remotes['origin'].url),
                    'path': abs_path,
                    'last_commit': str(subm_repo.head.target),
                    'name': repo.lookup_submodule(subm).name.rsplit('/', maxsplit=1)[-1]
                })
                self._submodules_info = result
        return self._submodules_info

    def get_submodule_name_by_path(self, path: str):
        for subm_info in self.submodules_info:
            if subm_info.get('path') in path:
                return subm_info.get('name')
        return None

    def get_self_view(self):
        self.views = self.get_all_views_from_app()
        self.find_app_endpoints()

    def create_doc(self):
        for cls in self.views:
            if cls.methods:
                self.create_doc_with_table(cls)

    def create_api_calls(self, cls):
        self.cls = cls
        self.get_app_or_view_cls()
        self.get_self_view()
        self.sort()
        self.create_doc()

    @staticmethod
    def is_json(data):
        try:
            json_object = json.loads(data)
        except:
            return data
        return json.dumps(json_object, indent=4)

    @staticmethod
    def find_description(word, string):
        if string:
            description = re.search(rf"@{word}[\s\S]+?@\s{{1}}", string)
            if description:
                descr_group = description.group()[len(word) + 1:-2].strip()
                return descr_group
        return ""


class GetAPICallsDocumentationView(MethodView):
    """ 
    @POST Get API Calls from service@
    @POST_body_request
    Content-Type: None
    @
    @POST_body_response 
    {
        "doucmentation": {"/endpoint/": 
                            {"methods": 
                                {"GET": {"body_params": 
                                {"request_body": "", "response_body": ""},  
                                    "description": "string", 
                                    "git_link": "https://git.example.com/project/file.py#L54"},
                                "POST": {"body_params": 
                                    {"request_body": "\n  "service_uuid": "8abee553-cb08-4881-8d9a-4dc5de7b7098" ", "response_body": "status": "success"},
                                    "description": "string", 
                                    "git_link": "https://git.example.com/project/file.py#L54"}
                                } 
                                "view_func": "ExampleViewName", 
                                "submodule": null },
                            ...
                            }
                        }
    }
    @
    """
    
    @service_only
    @admin_only
    @cross_origin()
    def post(self):
        api_builder = ApiCallsBuilder()
        api_builder.create_api_calls(app)
        result = {
            'documentation': api_builder.json_doc
        }
        return make_response(jsonify(result), 200)


class SyncDocumentationBuilder(ApiCallsBuilder):

    def __init__(self):
        super().__init__()
        self.flow = list()
        self.root_path = os.getcwd()
        self.exclude_dirs = ('__pycache__', 'public', 'static', 'templates')
        self.exclude_python_files = ('__init__.py', 'routes.py', 'forms.py')

    def create_sync_documentation(self, cls):
        self.cls = cls
        self.get_app_or_view_cls()
        self.get_sync_flow()
        self.create_doc()

    def get_sync_flow(self):
        self.collect_sync_flow(self.app.root_path, self.flow)
        for submodule in self.submodules:
            self.collect_sync_flow(self.root_path + '/' + submodule, self.flow)

    def get_sync_flow_from_directory(self, dir_path):
        flow = []
        for path in os.listdir(dir_path):
            if '.py' in path and path not in self.exclude_python_files:
                py_file_path = dir_path + '/' + path
                with open(py_file_path, 'r') as f:
                    file_content = f.read()

                parsed_ast = ast.parse(file_content)
                for node in ast.walk(parsed_ast):
                    if isinstance(node, ast.ClassDef) or isinstance(node, ast.FunctionDef):
                        doc_strings = [str(attribute.value.value) for attribute in node.body
                                       if isinstance(attribute, ast.Expr)
                                       and isinstance(attribute.value, ast.Constant)]
                        sync_data = None
                        for string in doc_strings:
                            if 'SYNC' in string:
                                sync_data = json.loads(self.find_description('SYNC', string))
                                break

                        if sync_data:
                            git_link = self.create_git_file_link(py_file_path)
                            git_link += f'#L{node.lineno}'

                            flow.append({
                                'name': node.name,
                                'path': git_link,
                                'sync_data': sync_data
                            })
        return flow

    def collect_sync_flow(self, root_path, flow):
        dirs = sorted(os.listdir(root_path))

        if not dirs:
            return

        for directory in dirs:
            if directory in self.exclude_dirs:
                continue

            dir_path = root_path + '/' + directory
            if os.path.isdir(dir_path):
                sync_flow = self.get_sync_flow_from_directory(dir_path)
                if sync_flow:
                    flow += sync_flow
                    self.collect_sync_flow(dir_path, flow),
                else:
                    self.collect_sync_flow(dir_path, flow)
            else:
                continue

    def create_doc(self):
        sync_services = {}
        for entity in self.flow:
            sync_data = entity.pop('sync_data')
            flow_name = sync_data.pop('flow')
            flow_description = sync_data.pop('description', None)
            services = sync_data.pop('services')

            if services == 'all':
                entity_copy = entity.copy()
                if 'all' in sync_services:
                    if flow_name in sync_services['all']:
                        sync_services['all'][flow_name][entity_copy.pop('name')] = entity_copy

                        if flow_description and 'description' not in sync_services['all'][flow_name]:
                            sync_services['all'][flow_name]['description'] = flow_description

                    else:
                        flow_details = {
                            entity_copy.pop('name'): entity_copy
                        }
                        if flow_description:
                            flow_details['description'] = flow_description

                        sync_services['all'][flow_name] = flow_details

                else:
                    flow = {
                        flow_name: {entity_copy.pop('name'): entity_copy},
                        'all_names': self.get_all_services_names()
                    }
                    if flow_description:
                        flow[flow_name]['description'] = flow_description
                    sync_services['all'] = flow

            else:
                for service in services:
                    service_name = service.pop('name')
                    class_description = service.pop('description')
                    signature = service.pop('signature', None)

                    entity_copy = entity.copy()
                    entity_copy['description'] = class_description
                    if signature:
                        entity_copy['signature'] = signature

                    if service_name in sync_services:
                        existed_service = sync_services[service_name]

                        if flow_name in existed_service:
                            existed_service[flow_name][entity_copy.pop('name')] = entity_copy
                        else:
                            existed_service[flow_name] = {entity_copy.pop('name'): entity_copy}

                        if flow_description and 'description' not in existed_service[flow_name]:
                            existed_service[flow_name]['description'] = flow_description
                    else:
                        flow = {
                            flow_name: {entity_copy.pop('name'): entity_copy}
                        }
                        if flow_description:
                            flow[flow_name]['description'] = flow_description

                        sync_services[service_name] = flow

        self.json_doc = sync_services


class GetSyncDocumentationView(MethodView):
    """
    @POST Collect Sync documentation from service@
    @POST_body_request
    Content-Type: None
    @
    @POST_body_response
    {
        "flow": "Flow Name",
        "services": [
            {
                "name": "service name",
                "description": "string",
                "signature": {
                    "field_0": "value_0",
                    ... 
                }
            },
            ...
        ]
    }
    @
    """
    @service_only
    @admin_only
    @cross_origin()
    def post(self):
        sync_documentation_builder = SyncDocumentationBuilder()
        sync_documentation_builder.create_sync_documentation(app)
        result = {
            'documentation': sync_documentation_builder.json_doc
        }
        return make_response(jsonify(result), 200)
