import os 
import ast
import json
import subprocess

from ..actor import Actor
from ..documentation_view import ApiCallsBuilder


def get_service(service_uuid):
    try:
        service = Actor.objects.get(uuid=service_uuid)
    except:
        service = None
    return service


class SharedModelsDocumentationBuilder(ApiCallsBuilder):
    
    def __init__(self):
        super().__init__()
        self.shared_models = list()
        self.save_usages = dict()
        self.commented_save_usages = dict()
        self.unknown_save_usages = dict()
        self.root_path = os.getcwd()
        self.exclude_dirs = ('__pycache__', 'public', 'static', 'templates')
        self.exclude_python_files = ('__init__.py', 'routes.py', 'forms.py')

    def create_shared_models_documentation(self, cls):
        self.cls = cls
        self.get_app_or_view_cls()
        self.get_shared_models_usages()
        self.get_shared_models()
        self.create_doc()

    def get_shared_models_usages(self):
        self.collect_save_method_usages_with_shared_push_attribute()
        self.add_docstring_data_for_shared_models_usages()

    class ClassAndFunctionNodesFinderByLineNumber(ast.NodeVisitor):
        def __init__(self, target_line):
            self.target_line = target_line
            self.class_node = None
            self.function_node = None

        def visit(self, node):
            if hasattr(node, 'lineno') and node.lineno <= self.target_line <= node.end_lineno:
                if isinstance(node, ast.ClassDef):
                    self.class_node = node
                    for child_node in node.body:
                        if hasattr(child_node, 'lineno') \
                        and child_node.lineno <= self.target_line <= child_node.end_lineno \
                        and isinstance(child_node, ast.FunctionDef):
                            self.function_node = child_node
                elif isinstance(node, ast.FunctionDef):
                    self.function_node = node
            else:
                ast.NodeVisitor.visit(self, node)

    class DocstringFinderByLineNumber(ast.NodeVisitor):
        def __init__(self, target_line):
            self.target_line = target_line
            self.docstring = ''

        def visit(self, node):
            if isinstance(node, ast.Expr) \
            and node.end_lineno == self.target_line - 1 \
            and hasattr(node, 'value') \
            and isinstance(node.value, ast.Constant):
                self.docstring = node.value.value
            else:
                ast.NodeVisitor.visit(self, node)

    def collect_save_method_usages_with_shared_push_attribute(self):
        grep_command = ['grep', '-r', '-n', '--include=*.py', '.save(shared_push=True', self.app.root_path] 

        strings = subprocess.run(
            grep_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        ).stdout.decode('utf-8').split('\n')

        usages = {}
        commented_usages = {}
        for string in strings:
            if string:
                py_file_path, line, other = string.split(':', 2)
                if other.strip()[0] == '#':
                    if py_file_path in commented_usages:
                        commented_usages[py_file_path].append(int(line))
                    else:
                        commented_usages[py_file_path] = [int(line)]
                else:
                    if py_file_path in usages:
                        usages[py_file_path].append(int(line))
                    else:
                        usages[py_file_path] = [int(line)]

        self.save_usages = usages
        self.commented_save_usages = commented_usages

    def add_docstring_data_for_shared_models_usages(self):
        models_usages = {}
        for file_path, lines in self.save_usages.items():
            git_link = self.create_git_file_link(file_path)
            with open(file_path, 'r') as f:
                file_content = f.read()

            parsed_ast = ast.parse(file_content)
            for line in lines:
                finder = self.ClassAndFunctionNodesFinderByLineNumber(line)
                finder.visit(parsed_ast)
                class_node, function_node = finder.class_node, finder.function_node

                place = None
                docstring = None
                if function_node or class_node:
                    place = {
                        'class': class_node.name if class_node else None,
                        'function': function_node.name if function_node else None
                    }
                    finder = self.DocstringFinderByLineNumber(line)
                    finder.visit(function_node or class_node)
                    docstring = finder.docstring

                if 'shared_push' in docstring:
                    usage_data = json.loads(self.find_description('shared_push', docstring))
                    model_name = usage_data.pop('model_name', None)
                    description = usage_data.pop('description', None)

                    if model_name:
                        if model_name in models_usages:
                            models_usages[model_name][f'{git_link}#L{line}'] = {
                                'description': description,
                                'place': place
                            }
                        else:
                            models_usages[model_name] = {
                                f'{git_link}#L{line}': {
                                    'description': description,
                                    'place': place
                                }
                            }
                    else:
                        if file_path in self.unknown_save_usages:
                            self.unknown_save_usages[file_path].append(line)
                        else:
                            self.unknown_save_usages[file_path] = [line]
                else:
                    if file_path in self.unknown_save_usages:
                        self.unknown_save_usages[file_path].append(line)
                    else:
                        self.unknown_save_usages[file_path] = [line]
        self.save_usages = models_usages

    def get_shared_models(self):
        self.collect_shared_models(self.app.root_path, self.shared_models)
        for submodule in self.submodules:
            self.collect_shared_models(self.root_path + '/' + submodule, self.shared_models)

    def collect_shared_models(self, root_path, models):
        dirs = sorted(os.listdir(root_path))

        if not dirs:
            return

        for directory in dirs:
            if directory in self.exclude_dirs:
                continue

            dir_path = root_path + '/' + directory
            if os.path.isdir(dir_path):
                shared_models = self.get_shared_models_from_directory(dir_path)
                if shared_models:
                    models += shared_models
                    self.collect_shared_models(dir_path, models),
                else:
                    self.collect_shared_models(dir_path, models)
            else:
                continue

    def get_shared_models_from_directory(self, dir_path):
        models = []
        for path in os.listdir(dir_path):
            if '.py' in path and path not in self.exclude_python_files:
                py_file_path = dir_path + '/' + path
                with open(py_file_path, 'r') as f:
                    file_content = f.read()

                parsed_ast = ast.parse(file_content)
                for node in ast.walk(parsed_ast):
                    if isinstance(node, ast.ClassDef):
                        class_doc_strings = [str(attribute.value.value) for attribute in node.body
                                             if isinstance(attribute, ast.Expr)
                                             and isinstance(attribute.value, ast.Constant)]
                        model_data = None
                        for string in class_doc_strings:
                            if 'SHARED_MODEL' in string:
                                model_data = json.loads(self.find_description('SHARED_MODEL', string))
                                break

                        if model_data:
                            git_link = self.create_git_file_link(py_file_path)
                            git_link += f'#L{node.lineno}'
                            model_data['path'] = git_link

                            models.append({
                                'name': node.name,
                                'model_data': model_data
                            })
        return models

    def create_doc(self):
        documentation = {}
        for model in self.shared_models:
            model_name = model.pop('name')
            model_data = model.pop('model_data')
            description = model_data.pop('description', None)

            if usages := self.save_usages.get(model_name):
                model_data['usages'] = usages
            documentation[model_name] = {
                'params': model_data
            }
            if description:
                documentation[model_name]['description'] = description

        documentation['unknown_save_usages'] = {
            f'{self.create_git_file_link(path)}#L': lines for path, lines in self.unknown_save_usages.items()
        }

        documentation['commented_save_usages'] = {
            f'{self.create_git_file_link(path)}#L': lines  for path, lines in self.commented_save_usages.items()
        }

        self.json_doc = documentation
 