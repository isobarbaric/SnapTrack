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

    receipt_parser = ReceiptParser()
    database = NotionDB(notion_token, database_id)
    print(database.columns)

    # batch work??
    products_valid = False
    products = None

    attempt_number = 1
    while not products_valid:
        if attempt_number == 5:
            raise Exception("Unable to parse receipt")
        
        print(f"Attempt Number #{attempt_number}")

        products = receipt_parser.parse(
            filepath = "../../data/receipts/receipt3.jpg", 
            columns = database.columns, 
            select_options = database.select_options
        )

        if len(products) != 0:
            products_valid = True

        attempt_number += 1

        print(f"Entries obtained: {products}\n")
        time.sleep(1)

    for product in products:
        print(product)
        database.add_row(product)

    end = time.time()
    print(f'\n{end - start} seconds elapsed')

if __name__ == '__main__':
    main()