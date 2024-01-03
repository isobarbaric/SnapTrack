from datetime import datetime
from notion_client import Client

class NotionDB:

    def __init__(self, notion_token, database_id):
        self.notion = Client(auth = notion_token)
        self.database_id = database_id

        self.structure = self.notion.databases.retrieve(self.database_id)

        # column headers by name
        self.pages = self.notion.databases.query(self.database_id)
        self._columns = list(self.pages['results'][0]['properties'].keys())

        self.select_options = {}

        # column headers by name, and includes types
        self.columns = self.get_columns()

    # change so doesn't rely on the first row existing
    def get_columns(self):
        # doesn't support checkbox, relation, rollup, formula, file
        # these are not relevant for finance tracking, so should be fine

        columns = []
        page_content = self.pages['results'][0]['properties']

        for column in self._columns:
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

            value = {'name': column, 'type': curr_column['type']}
            columns.append(value)

            if curr_column['type'] in ['select', 'multi_select']:
                self.select_options[column] = [option['name'] for option in self.structure['properties'][column]['multi_select']['options']]

        return columns

    def add_row(self, date: datetime, place, what, amount):
        self.notion.pages.create(
            parent = {'database_id': self.database_id},
            properties = {
                'Date': {'date': {'start': str(date).split()[0]}},
                'Place': {'title':  [{'text': {'content': place}}]},
                'What': {'multi_select': [{'name': what}]},
                'Amount': {'number': amount}
            }   
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
