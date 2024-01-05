import click
import colorama
from colorama import Fore
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

# if verbose, show time elapsed stuff
@click.command()
@click.argument('filepath', type=click.Path(exists=True), nargs=1)
@click.option('--verbose', '-v', is_flag=True, help='Show time elapsed for each operation')
def send_receipt(filepath, verbose):
    """Send receipt to Notion database"""
    spinner = yaspin(text="Processing...", color="yellow")

    if verbose:
        add_receipt(filepath, spinner, verbose=True)
    else:
        add_receipt(filepath, spinner, verbose=False)

def add_receipt(filepath: str, spinner: yaspin, verbose: bool):
    start = time.time()
    
    receipt_parser = ReceiptParser(spinner, verbose)
    database = NotionDB(notion_token, database_id, spinner)

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

    # print("\n=========\nProducts:\n=========")
    spinner.text = "Adding entries to database..."
    for product in products:
        # print(product)
        database.add_row(product)
    end = time.time()
    spinner.stop()

    if verbose:
        spinner.write(Fore.BLUE + f"[Total time elapsed: {'{:.3f}'.format(end - start)}" + " seconds]" + Fore.RESET)
    # print(f'\nTotal: {end - start} seconds elapsed')

    spinner.text = ''
    spinner.ok(Fore.GREEN + "🎉 Receipt details sent to database" + Fore.RESET)

if __name__ == '__main__':
    send_receipt()
