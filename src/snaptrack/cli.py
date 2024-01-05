from dotenv import load_dotenv
import os
from snaptrack.receipt_parser import ReceiptParser
from snaptrack.notion import NotionDB
import time

# load environment variables
load_dotenv()

notion_token = os.environ["NOTION_TOKEN"]
database_id = os.environ["NOTION_DATABASE_ID"]

def main():
    start = time.time()
    
    receipt_parser = ReceiptParser()
    database = NotionDB(notion_token, database_id)
    # print(database.columns)

    products_valid = False
    products = None

    attempt_number = 1
    while not products_valid:
        if attempt_number == 5:
            raise Exception("Unable to parse receipt")
        
        products = receipt_parser.parse(
            filepath = "../../data/receipts/receipt3.jpg", 
            columns = database.columns, 
            select_options = database.select_options
        )

        if len(products) != 0:
            products_valid = True

        attempt_number += 1
        time.sleep(1)

    print("\n=========\nProducts:\n=========")
    for product in products:
        print(product)
        database.add_row(product)

    end = time.time()
    print(f'\nTotal: {end - start} seconds elapsed')

if __name__ == '__main__':
    main()