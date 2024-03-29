from datetime import datetime
from notion_client import Client

class NotionDBError(Exception):
    """Error class for the NotionDB class
    """

    def __init__(self, error_msg):
        self.message = error_msg
        super().__init__(self.message)

class NotionDB:
    """Notion database manager
    """

    def __init__(self, notion_token, database_id, spinner):
        self.notion = Client(auth = notion_token)
        self.database_id = database_id
        self.spinner = spinner

        # structure of database
        self.structure = self.notion.databases.retrieve(self.database_id)
        # print(self.structure)

        # TODO: get column headers using retrieve
        # column headers by name
        self.pages = self.notion.databases.query(self.database_id)

        try:
            self._columns = list(self.pages['results'][0]['properties'].keys())
        except Exception:
            self.spinner.fail("❌ no existing entries in database")
            raise NotionDBError(error_msg="There are no existing entries in database, unable to get column headers")

        # saving options for the columns that are select or multi-select
        self.select_options = {}

        # column headers by name, and also includes types
        self.columns = self.get_columns()

    def get_columns(self):
        # doesn't support checkbox, relation, rollup, formula, file (not relevant for finance tracking)
        properties = self.structure['properties']
        columns = []        

        for key in properties:
            column_name = properties[key]['name'].title()

            if properties[key]['type'] == 'select':
                self.select_options[properties[key]['name']] = [option['name'] for option in self.structure['properties'][column_name]['select']['options']]

            if properties[key]['type'] == 'multi_select':
                self.select_options[properties[key]['name']] = [option['name'] for option in self.structure['properties'][column_name]['multi_select']['options']]
                
            value = {'name': properties[key]['name'], 'type': properties[key]['type']}
            columns.append(value)

        return columns

    def add_row(self, row_content):
        properties = {}

        for column in self.columns:
            column_name = column['name']
            column_type = column['type']

            # in case GPT doesn't include this element
            if column_name not in row_content:
                row_content[column_name] = ''

            # getting value from row_content, and getting the right capitalization
            if column_type == 'multi_select':
                value = row_content[column_name]
            else:
                value = str(row_content[column_name]).title()

            # building properties dictionary for different types required different formatting
            if column_type == 'title':
                properties[column_name] = {'title': [{'text': {'content': str(value)}}]}
            elif column_type == 'text':
                properties[column_name] = {'text': {'content': str(value)}}
            elif column_type == 'rich_text':
                properties[column_name] = {'rich_text': [{'text': {'content': str(value)}}]}
            elif column_type == 'number':
                number = str(value)
                if number != '':
                    unwanted_entities = [',','$','€','£','¥','A$','CA$','CHF','CN¥','kr','NZ$']
                    for entity in unwanted_entities:
                        number = number.replace(entity, '')
                    try:
                        properties[column_name] = {'number': float(number)}
                    except Exception:
                        properties[column_name] = {'number': None}
                else:
                    properties[column_name] = {'number': None}
            elif column_type == 'select':
                if value == '':
                    continue
                properties[column_name] = {'select': {'name': str(value)}}
            elif column_type == 'date':
                date = str(value)
                if date == '':
                    continue
                try:
                    if date != '' and date is not None and date != 'N/A':               
                        # extracting date from date incase time is included
                        date = str(date).split()[0]
                        date = datetime.strptime(date, '%Y/%m/%d')
                        date = str(date).split()[0]
                except Exception:
                    continue
                properties[column_name] = {'date': {'start': date, 'end': None}}
            elif column_type == 'url':
                properties[column_name] = {'url': str(value)}
            elif column_type == 'email':
                properties[column_name] = {'email': str(value)}
            elif column_type == 'phone_number':
                properties[column_name] = {'phone_number': str(value)}
            elif column_type == 'multi_select':
                try:
                    assert isinstance(value, list)
                except AssertionError as ex:
                    raise NotionDBError(error_msg=f"Value for multi_select column {column_name} must be a list (GPT)") from ex     
                properties[column_name] = {'multi_select': [{'name': single_value} for single_value in value if single_value != '']}

        try:
            self.notion.pages.create(
                parent = {'database_id': self.database_id},
                properties = properties
            )
        except Exception as ex:
            self.spinner.fail("❌ unable to add row(s) to database")
            raise NotionDBError(error_msg="Unable to add row to database") from ex

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
