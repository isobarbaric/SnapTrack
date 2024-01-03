from datetime import datetime, timezone
from dotenv import load_dotenv
from snaptrack.notion import NotionDB
import os

# load environment variables
load_dotenv()

notion_token = os.environ["NOTION_TOKEN"]
database_id = os.environ["NOTION_DATABASE_ID"]

db = NotionDB(notion_token, database_id)

db.print()
# db.add_row(datetime.now(timezone.utc), "Textbook", "Study", 12.99)
# print(db.columns)
