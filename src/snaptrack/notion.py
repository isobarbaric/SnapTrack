from datetime import datetime, timezone
from dotenv import load_dotenv
import json
import requests
import os

load_dotenv()

headers = {
    'Authorization': 'Bearer ' + os.getenv("NOTION_SECRET"),
    'Content-Type': 'application/json',
    'Notion-Version': '2022-06-28'
}

# get all pages
def get_pages():
    url = f'https://api.notion.com/v1/databases/{os.getenv("NOTION_DATABASE_ID")}/query'

    # get all pages possible
    payload = {'page_size': 100}

    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    results = data['results']

    with open('../../test/notion-response.json', 'w') as db:
        json.dump(data, db, indent=4)

    results = data['results']
    return results

pages = get_pages()

# read entries from database
for page in pages:
    page_id = page['id']
    props = page['properties']

    date = props['Date']['date']['start']
    date = datetime.fromisoformat(date)

    place = props['Place']['title'][0]['text']['content']
    what = props['What']['multi_select'][0]['name']
    amount = props['Amount']['number']

    print(date, place, what, amount)
