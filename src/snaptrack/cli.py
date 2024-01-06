import click
import colorama
from colorama import Fore
from dotenv import load_dotenv
import keyring
import os
import json
from snaptrack.receipt_parser import ReceiptParser
from snaptrack.notion import NotionDB
import time
from yaspin import yaspin

# load environment variables
load_dotenv()

notion_token = os.environ["NOTION_TOKEN"]
database_id = os.environ["NOTION_DATABASE_ID"]

def load_credentials():
    # getting user's input to set credentials
    openai_api_key = click.prompt("Enter your OpenAI API key", hide_input=True)
    notion_token = click.prompt("Enter your Notion API token", hide_input=True)
    database_id = click.prompt("Enter the specific Notion database ID", hide_input=True)

    # adding passwords to keyring
    keyring.set_password("snaptrack", "openai_api_key", openai_api_key)
    keyring.set_password("snaptrack", "notion_token", notion_token)
    keyring.set_password("snaptrack", "database_id", database_id)

@click.command()
@click.argument('filepath', type=click.Path(exists=True), nargs=1)
@click.option('--verbose', '-v', is_flag=True, help='Show time elapsed for each operation')
def send_receipt(filepath, verbose):
    """Send receipt to Notion database"""
    spinner = yaspin(text="Processing...", color="yellow")

    # if details don't exist already, prompt user to set them
    if keyring.get_password("snaptrack", "openai_api_key") is None:
        spinner.write("Thank you for using SnapTrack. First time setup detected. To get started, please enter your OpenAI API token, Notion API token and specific Notion database ID.")
        load_credentials()
    
    if verbose:
        add_receipt(filepath, spinner, verbose=True)
    else:
        add_receipt(filepath, spinner, verbose=False)

def add_receipt(filepath: str, spinner: yaspin, verbose: bool):
    start = time.time()

    # loading credentials from keyring    
    openai_api_key = keyring.get_password("snaptrack", "openai_api_key")
    notion_token = keyring.get_password("snaptrack", "notion_token")
    database_id = keyring.get_password("snaptrack", "database_id")

    receipt_parser = ReceiptParser(openai_api_key, spinner, verbose)
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

    spinner.text = "Adding entries to database..."
    for product in products:
        database.add_row(product)
    end = time.time()
    spinner.stop()

    if verbose:
        spinner.write(Fore.BLUE + f"[Total time elapsed: {'{:.3f}'.format(end - start)}" + " seconds]" + Fore.RESET)

    spinner.text = ''
    spinner.ok(Fore.GREEN + "🎉 Receipt details sent to database" + Fore.RESET)

if __name__ == '__main__':
    send_receipt()
