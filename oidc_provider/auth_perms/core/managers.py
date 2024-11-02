from psycopg2 import sql
from .exceptions import FieldError
from .database.manager import DatabaseManager


class BaseManager:

    def __init__(self, table_name, *args, **kwargs):
        self.table_name = table_name

    def compile_query(self, *args, **kwargs):

        appends_list = list()
        values = dict()

        if not args:
            query_string = "SELECT * FROM {} "
        else:
            query_string = "SELECT " + ", ".join(['{}' for _ in args]) + "FROM {}"
            appends_list += list(args)
        appends_list.append(sql.Identifier(self.table_name))

        if kwargs:
            query_string += "WHERE "

        for k, v in kwargs.items():

            query_fragment, appends, value = self.parse_keyword(k, v)
            query_string += query_fragment
            query_string += " AND "
            appends_list += appends
            values.update(value)

        else:
            query_string = query_string.rstrip('AND ')

        query = sql.SQL(query_string).format(*appends_list)

        return query, values

    def exists_query(self, *args, **kwargs):

        appends_list = list()
        values = dict()
        query_string = "SELECT EXISTS(SELECT 1 FROM {} "

        appends_list.append(sql.Identifier(self.table_name))

        if kwargs:
            query_string += "WHERE "

        for k, v in kwargs.items():

            query_fragment, appends, value = self.parse_keyword(k, v)

            query_string += query_fragment
            query_string += " AND "
            appends_list += appends
            values.update(value)

        else:
            query_string = query_string.rstrip('AND ')

        query_string += ')'

        query = sql.SQL(query_string).format(*appends_list)

        return query, values

    @staticmethod
    def parse_keyword(attribute, value):

        elements = attribute.split('__')

        if len(elements) == 1:
            return '{}={}', [sql.Identifier(attribute), sql.Placeholder(attribute)], {attribute: value}

        elif len(elements) == 2:

            if elements[1] == 'in':
                attribute = elements[0]
                return '{} IN {}', [sql.Identifier(attribute), sql.Placeholder(attribute)], {attribute: tuple(value)}

            elif elements[1] == 'contains':
                value = '%' + value + '%'
                attribute = elements[0]
                return '{} LIKE {}', [sql.Identifier(attribute), sql.Placeholder(attribute)], {attribute: value}

        raise FieldError('Unsupported lookup')
