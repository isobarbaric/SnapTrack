from datetime import datetime, timezone
from dotenv import load_dotenv
from notion_client import Client
import os

# load environment variables
load_dotenv()

notion_token = os.environ["NOTION_TOKEN"]
database_id = os.environ["NOTION_DATABASE_ID"]

def main():
    notion = Client(auth = notion_token)

    add_row(notion, datetime.now(timezone.utc), "Walmart", "Food", 362.58)

    # get pages from database
    pages = notion.databases.query(database_id)

    for page in pages['results']:
        properties = page['properties']

        date = properties['Date']['date']['start']
        place = properties['Place']['title'][0]['text']['content']
        what = properties['What']['multi_select'][0]['name']
        amount = properties['Amount']['number']

        print(date, place, what, amount)

def get_categories(client):
    pages = client.databases.query(database_id)
    categories = []

    for page in pages['results']:
        properties = page['properties']
        category = properties['What']['multi_select'][0]['name']
        categories.append(category)

    return categories

def add_row(client, date: datetime, place, what, amount):
    client.pages.create(
        parent = {'database_id': database_id},
        properties = {
            'Date': {'date': {'start': str(date).split()[0]}},
            'Place': {'title':  [{'text': {'content': place}}]},
            'What': {'multi_select': [{'name': what}]},
            'Amount': {'number': amount}
        }   
    )

if __name__ == '__main__':
    main()
