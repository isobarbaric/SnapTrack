import click
from dotenv import load_dotenv
import os
from snaptrack.receipt_parser import ReceiptParser
from snaptrack.notion import NotionDB
import time
from yaspin import yaspin

# load environment variables
load_dotenv()

notion_token = os.environ["NOTION_TOKEN"]
database_id = os.environ["NOTION_DATABASE_ID"]

@click.command()
@click.argument('filepath', type=click.Path(exists=True), nargs=1)
def send_receipt(filepath):
    """Send receipt to Notion database"""
    with yaspin(text="Processing...", color="yellow") as spinner:
        add_receipt(filepath)

def add_receipt(filepath: str):
    start = time.time()
    
    receipt_parser = ReceiptParser()
    database = NotionDB(notion_token, database_id)

    products_valid = False
    products = None

    attempt_number = 1
    while not products_valid:
        if attempt_number == 5:
            raise Exception("Unable to parse receipt")
        
        products = receipt_parser.parse(
            filepath = filepath, 
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
    send_receipt()
