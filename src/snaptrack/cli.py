import click
import colorama
from colorama import Fore
from dotenv import load_dotenv
import os
import json
from snaptrack.receipt_parser import ReceiptParser
from snaptrack.notion import NotionDB
import time
from yaspin import yaspin

CONFIG_FILE = 'config.json'

# load environment variables
load_dotenv()

# TODO: create pydantic model for config

notion_token = os.environ["NOTION_TOKEN"]
database_id = os.environ["NOTION_DATABASE_ID"]

# config functions

def get_config():
    config = {
        'OPENAI_API_KEY': click.prompt("Enter your OpenAI API key", hide_input=True),
        'NOTION_TOKEN': click.prompt("Enter your Notion API token", hide_input=True),
        'NOTION_DATABASE_ID': click.prompt("Enter your Notion Database ID", hide_input=True)
    }
    with open(CONFIG_FILE, 'w') as file:
        json.dump(config, file, indent=4)

def load_config():
    with open(CONFIG_FILE, 'r') as file:
        return json.load(file)


@click.command()
@click.argument('filepath', type=click.Path(exists=True), nargs=1)
@click.option('--verbose', '-v', is_flag=True, help='Show time elapsed for each operation')
def send_receipt(filepath, verbose):
    """Send receipt to Notion database"""
    spinner = yaspin(text="Processing...", color="yellow")

    # if config file doesn't exist, create one
    if not os.path.exists(CONFIG_FILE):
        spinner.write("Thank you for using SnapTrack. First time setup detected. To get started, please enter your OpenAI API token, Notion API token and specific Notion database ID.")
        get_config()

    if verbose:
        add_receipt(filepath, spinner, verbose=True)
    else:
        add_receipt(filepath, spinner, verbose=False)

def add_receipt(filepath: str, spinner: yaspin, verbose: bool):
    start = time.time()

    # load configuration details
    config = load_config()

    receipt_parser = ReceiptParser(config['OPENAI_API_KEY'], spinner, verbose)
    database = NotionDB(config['NOTION_TOKEN'], config['NOTION_DATABASE_ID'], spinner)

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
