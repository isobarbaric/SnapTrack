from datetime import datetime
from notion_client import Client

class NotionDB:

    def __init__(self, notion_token, database_id):
        self.notion = Client(auth = notion_token)
        self.database_id = database_id

    def print(self):
        pages = self.notion.databases.query(self.database_id)
        for page in pages['results']:
            page_content = page['properties']

            date = page_content['Date']['date']['start']
            place = page_content['Place']['title'][0]['text']['content']
            what = page_content['What']['multi_select'][0]['name']
            amount = page_content['Amount']['number']
            print(date, place, what, amount)

    def get_columns(self):
        pages = self.notion.databases.query(self.database_id)
        cols = pages['results'][0]['properties'].keys()
        return list(cols)

    def add_row(self, date: datetime, place, what, amount):
        # TODO: add relevant notion icon
        
        self.notion.pages.create(
            parent = {'database_id': self.database_id},
            properties = {
                'Date': {'date': {'start': str(date).split()[0]}},
                'Place': {'title':  [{'text': {'content': place}}]},
                'What': {'multi_select': [{'name': what}]},
                'Amount': {'number': amount}
            }   
        )
