from dotenv import load_dotenv
import os
from snaptrack.receipt_parser import ReceiptParser
from snaptrack.notion import NotionDB

load_dotenv()

notion_token = os.environ["NOTION_TOKEN"]
database_id = os.environ["NOTION_DATABASE_ID"]

def main():
    db = NotionDB(notion_token, database_id)
    receipt_parser = ReceiptParser()

    # print(db.select_options)

    products = receipt_parser.parse(filepath = "../../data/receipts/receipt3.jpg", 
                                    categories = db.columns, 
                                    select_options = db.select_options)
    print(db.columns)
    # print(products)

    for product in products:
        db.add_row(product)

if __name__ == '__main__':
    main()