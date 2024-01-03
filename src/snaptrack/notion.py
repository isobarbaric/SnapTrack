from datetime import datetime
from notion_client import Client

class NotionDBError(Exception):
    def __init__(self, exception):
        exception_str = str(exception)
        self.message = f"{type(exception).__name__}: {exception_str}"
        super().__init__(self.message)

class NotionDB:

    def __init__(self, notion_token, database_id):
        self.notion = Client(auth = notion_token)
        self.database_id = database_id

        # structure of database
        self.structure = self.notion.databases.retrieve(self.database_id)
        # print(self.structure)

        # column headers by name
        self.pages = self.notion.databases.query(self.database_id)
        self._columns = list(self.pages['results'][0]['properties'].keys())

        # saving options for the columns that are select or multi-select
        self.select_options = {}

        # column headers by name, and also includes types
        self.columns = self.get_columns()

    def get_columns(self):
        # doesn't support checkbox, relation, rollup, formula, file
        # these are not relevant for finance tracking, so should be fine

        columns = []        
        properties = self.structure['properties']

        for key in properties:
            column_name = properties[key]['name']

            if properties[key]['type'] == 'select':
                self.select_options[properties[key]['name']] = [option['name'] for option in self.structure['properties'][column_name]['select']['options']]

            if properties[key]['type'] == 'multi_select':
                self.select_options[properties[key]['name']] = [option['name'] for option in self.structure['properties'][column_name]['multi_select']['options']]
                
            value = {'name': properties[key]['name'], 'type': properties[key]['type']}
            columns.append(value)

        return columns

    def add_row(self, row_content):
        # build properties dictionary
        properties = {}

        for column in self.columns:
            column_name = column['name']
            column_type = column['type']

            value = row_content[column_name]
            print(f'{column_name}: {value}\n')

            try:
                # building properties dictionary for different types required different formatting
                if column_type == 'title':
                    properties[column_name] = {'title': [{'text': {'content': str(value)}}]}
                elif column_type == 'text':
                    properties[column_name] = {'text': {'content': str(value)}}
                elif column_type == 'number':
                    number = str(value)                
                    unwanted_entities = [',','$','€','£','¥','A$','CA$','CHF','CN¥','kr','NZ$']
                    for entity in unwanted_entities:
                        number = number.replace(entity, '')

                    properties[column_name] = {'number': float(number)}
                elif column_type == 'select':
                    properties[column_name] = {'select': {'name': str(value)}}
                elif column_type == 'date':
                    date = str(value).split()[0]
                    date = datetime.strptime(date, "%Y/%m/%d")
                    # print(f'Date: {date}')
                    properties[column_name] = {'date': {'start': str(date), 'end': None}}
                elif column_type == 'url':
                    properties[column_name] = {'url': str(value)}
                elif column_type == 'email':
                    properties[column_name] = {'email': str(value)}
                elif column_type == 'phone_number':
                    properties[column_name] = {'phone_number': str(value)}
                elif column_type == 'title':
                    properties[column_name] = {'title': [{'text': {'content': str(value)}}]}
                elif column_type == 'multi_select':
                    properties[column_name] = {'multi_select': [{'name': single_value} for single_value in value]}
            
            except Exception as e:
                raise NotionDBError(e)

        print(properties)

        self.notion.pages.create(
            parent = {'database_id': self.database_id},
            properties = properties
        )

    def print(self):
        database_row = []

        for page in self.pages['results']:
            page_content = page['properties']
            page_row = []

            for column in self.columns:
                curr_column = page_content[column]

                value = None
                if curr_column['type'] == 'text':
                    value = curr_column['text']['content']
                elif curr_column['type'] == 'number':
                    value = curr_column['number']
                elif curr_column['type'] == 'select':
                    value = curr_column['select']['name']
                elif curr_column['type'] == 'date':
                    value = curr_column['date']['start']
                elif curr_column['type'] == 'url':
                    value = curr_column['url']
                elif curr_column['type'] == 'email':
                    value = curr_column['email']
                elif curr_column['type'] == 'phone_number':
                    value = curr_column['phone_number']
                elif curr_column['type'] == 'title':
                    value = curr_column['title'][0]['text']['content']
                elif curr_column['type'] == 'multi_select':
                    value = curr_column['multi_select'][0]['name']

                value = {column: value}
                page_row.append(value)

            database_row.append(page_row)

        for row in database_row:
            print(row)
