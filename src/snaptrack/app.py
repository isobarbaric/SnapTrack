from dotenv import load_dotenv
import os
from snaptrack.receipt_parser import ReceiptParser
from snaptrack.notion import NotionDB
import time

load_dotenv()

notion_token = os.environ["NOTION_TOKEN"]
database_id = os.environ["NOTION_DATABASE_ID"]

def main():
    start = time.time()

    db = NotionDB(notion_token, database_id)
    receipt_parser = ReceiptParser()
    # print(db.columns)
    # print(db.select_options)

    products = receipt_parser.parse(filepath = "../../data/receipts/receipt4.jpg", 
                                    columns = db.columns, 
                                    select_options = db.select_options)
    # print(products)

    # select_fields = db.select_options.keys()
    # print(select_fields)
    for product in products:
        print(product)
        db.add_row(product)

    end = time.time()
    print(f'\n{end - start} seconds elapsed')

if __name__ == '__main__':
    main()