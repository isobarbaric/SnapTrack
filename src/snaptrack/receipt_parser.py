import os
import re
import ast
import json
import boto3
import time
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from openai import OpenAI

# loading api key
load_dotenv()

# initializing OpenAI client
openai_client = OpenAI(api_key = os.environ["OPENAI_API_KEY"])

class ReceiptParserError(Exception):
    def __init__(self, exception, include_name=True):
        exception_str = str(exception)
        if include_name:
            self.message = f"{type(exception).__name__}: {exception_str}"
        else:
            self.message = exception_str
        super().__init__(self.message)

class ReceiptParser:

    def __init__(self):
        pass

    def get_rekognition_response(self, filepath):
        """Gets AWS Rekognition response for a specified image

        :param filename: name of image file
        :type filename: str
        :return: a AWS Rekognition result
        :rtype: JSON dictionary
        """
        try:
            session = boto3.Session(profile_name='default')
            aws_client = session.client('rekognition')

            with open(filepath, 'rb') as image_file:
                image_data = image_file.read()

            # call Amazon Rekognition API
            response = aws_client.detect_text(Image={'Bytes': image_data})

        except ClientError as e:
            response = {'Error': str(e)}

        return response

    def parse_rekognition_response(self, aws_response, columns, select_options = None):
        """Parses receipt and returns JSON dictionary 

        :param aws_response: a AWS Rekognition result
        :type aws_response: JSON dictionary
        :param columns: a list of columns to parse for, stuctured as {column_name: column_type}
        :type columns: list of dictionaries
        :return: a list of items contained in the receipt
        :rtype: JSON dictionary
        """

        def get_target_column(target):
            for item in columns:
                if item['name'] == target:
                    return item
            return -1

        # clean up response to only include text content
        aws_text = [elem['DetectedText'] for elem in aws_response['TextDetections']]

        # building a list of all of the text items on the receipt
        receipt_list = "["
        for item in aws_text[:-1]:
            receipt_list += f"{item}, "
        receipt_list += f"{aws_text[-1]}]"
        
        print("\n1. Working on extracting page features for non-selection columns...")

        # passing prompt to GPT-3.5 and gettings its response
        non_select_time_start = time.time()

        valid_gpt_response = False
        while not valid_gpt_response:
            entries = self.add_non_select_columns(receipt_list, columns)
            if 'Error' not in entries:
                valid_gpt_response = True
            # print(f"Entries obtained via GPT: {entries}\n")
        non_select_time_end = time.time()

        print(f"\n=> Time elapsed for non-selection columns: {non_select_time_end - non_select_time_start} seconds")
                
        entry_history = [len(entries)]

        print("\n2. Working on extracting page features for selection columns...")

        select_time_start = time.time()
        select_column_names = list(select_options.keys())
        for column_name in list(select_column_names):
            target = get_target_column(column_name)
            # print(f'...current column: {column_name}')
            if target['type'] == 'select':
                self.add_select_column(entries, column_name, 'select', select_options[column_name])
            else:
                self.add_select_column(entries, column_name, 'multi_select', select_options[column_name])
        select_time_end = time.time()
        print(f"\n=> Time elapsed for selection columns: {select_time_end - select_time_start} seconds")

        entry_history.append(len(entries))

        # print(f"Entries before filtering: {entries}")
        print("\n3. Filtering pages to get the best results...")

        filtration_time_start = time.time()

        # TODO: clean up this function, consolidate with filter_non_select_cols
        # non_select_columns = []
        # for column in columns:
        #     if not column['type'] in ['select', 'multi_select']:
        #         non_select_columns.append(column['name'])
 
        # # change this filtering to check for non-text content
        # filtered_entries = []
        # for purchase in entries:
        #     num_empty = 0
        #     for column in non_select_columns:
        #         if purchase[column] == '':
        #             num_empty += 1
        #     if num_empty <= int(len(columns)/2):
        #         filtered_entries.append(purchase)

        filtered_entries = self.filter_content(entries, columns)

        # filtered_entries = self.filter_select_cols(entries, columns)

        # entry_history.append(len(filtered_entries))
        # filtered_entries = self.filter_non_select_cols(filtered_entries, columns)
        # entry_history.append(len(filtered_entries))

        # print(f"Entries after filtering: {filtered_entries}")

        filtration_time_end = time.time()
        print(f"\n=> Time elapsed for filtration: {filtration_time_end - filtration_time_start} seconds")

        # check if lens is non-increasing
        if entry_history != sorted(entry_history, reverse=True):
            raise ReceiptParserError(f"Entries lost in processing", include_name=False)

        return filtered_entries

    def get_gpt_response(self, prompt, as_json=True):
        prompt = "Limit your response to under 80 tokens for times' sake AND 15 sceonds response time. " + prompt
        if as_json:
            gpt_response = openai_client.chat.completions.create(
                messages = [
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model = "gpt-3.5-turbo",
                temperature = 0.0
            )

            message = gpt_response.choices[0].message
            # print(message)
            # print(f"GPT-3.5 response: {message}")

            try:
                # details = json.loads(message)
                details = json.loads(message.content)
            except json.decoder.JSONDecodeError as e:
                details = {'Error': e}
            
            return details
        else:
            gpt_response = openai_client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model="gpt-3.5-turbo",
                temperature = 0.0
            )

            message = gpt_response.choices[0].message
            # print(message)
            
            return message.content

    def add_non_select_columns(self, receipt_list, columns):
        # created a detailed prompt for task
        prompt = "There are labels that represent columns in a Notion database. Scrutinize all extracted text for each entry in the receipt and assign them to appropriate labels (don't create your own labels, only create keys for given labels). For a particular product, assign a label an empty string if you are unsure what value should be assigned, but make sure to ALWAYS include every label for a particular entry. Please include dates in %Y/%m/%d format excluding time, and correct the content in a title word format. Make sure each entry has the same date (receipt will have a single date on it somewhere). Your output should ONLY be a list of JSON objects and nothing else. Don't list payment details, vendor details as separate purchases. This list is text extracted from a paper receipt: "

        # adding items on receipt to prompt
        prompt += receipt_list

        column_details = ''
        for column in columns:
            if column['type'] in ['select', 'multi_select']:
                continue
            column_details += f"\n- {column['name']} "

        prompt += column_details

        gpt_response_time_start = time.time()
        # print("initiated GPT-3.5 request")
        response = self.get_gpt_response(prompt)
        # print("received GPT-3.5 response")

        # print(response)

        gpt_response_time_end = time.time()
        # print(f"\n=> Time elapsed for GPT-3.5 response (non-selection): {gpt_response_time_end - gpt_response_time_start} seconds")

        return response

    def add_select_column(self, entries, column_name, column_type, options):
        if column_type not in ['select', 'multi_select']:
            raise ReceiptParserError(f"Invalid column type {column_type} passed as selection column", include_name=False)

        if column_type == 'select':
            prompt = "We are working with a Notion database that has a column of type 'Select'. The goal is to select upto one (you can choose zero) of the following options based on whether you believe they are related to the specific purchase entry or not. Do not create your own options, only choose from the ones provided. Respond WITH ONLY a SINGLE WORD, i.e. the option you choose. Please don't say anything else. Your options are: "
        elif column_type == 'multi_select':
            prompt = "We are working with a Notion database that has a column of type 'Multi-select'. The goal is to select multiple of the following options (return your selection as a list) based on whether you believe they are related to the specific purchase entry or not. Do not create your own options, only choose from the ones provided. Respond with a PYTHON LIST OF WORDS, i.e. the options you choose. Remember to put quotation marks around the words in that list to ensure it is syntatically correct Python. Please don't say anything else. Your options are: "

        if len(options) == 0:
            return ReceiptParserError(f"No options provided for column {column_name}", include_name=False)

        criteria = ''.join([f'{option}, ' for option in options][:-1]) + options[-1]
        prompt += criteria

        mod_entries = []
        for entry in entries:
            curr_prompt = prompt + f"\n And the current entry in question is: {entry}"
            curr_gpt_response = self.get_gpt_response(curr_prompt, as_json=False)
            unmodified_entry = entry

            if column_type == 'select':
                unmodified_entry[column_name] = curr_gpt_response
            else:
                try:
                    unmodified_entry[column_name] = ast.literal_eval(curr_gpt_response)
                except Exception:
                    print(f"Error: {curr_gpt_response}")
                    raise ReceiptParserError(f"Unable to parse GPT response {curr_gpt_response} as a list", include_name=False)
            mod_entries.append(unmodified_entry)

        return mod_entries

    def filter_content(self, entries, columns):
        filtered_entries = self.filter_select_cols(entries, columns)
        return self.filter_non_select_cols(filtered_entries, columns)

    def filter_non_select_cols(self, entries, columns):        
        def contains_unwanted_content(entry_column):
            lower_input = entry_column.lower()

            unwanted = ['tax', 'change', 'cash', 'card', 'amount', 'total', 'subtotal', 'discount', 'hst', 'gst', 'invoice', 'purchase', 'customer', 'receipt', 'round', 'balance', '.com', '.ca', 'feedback', 'swipe', 'sale', 'pay', 'shop', '*', 'approved', 'auth', 'record', 'important', 'you', 'copy']
            for word in unwanted:
                if word in lower_input:
                    return True

            unwanted_patterns = [
                # date
                r'\d{1,2}/\d{1,2}/\d{2,4}',
                # amount
                r'^\d+(\.\d{2})?$',
                # time
                r'\b\d{1,2}:\d{2}(?::\d{2})?\b',
                # phone number
                r'\d{10}',
                # URL
                r'https?://\S+',
                # credit card
                r'\b(?:\d[ -]*?){13,16}\b',
                r'\b(?:\d[ -]x?){13,16}\b'
            ]
            for pattern in unwanted_patterns:
                if re.search(pattern, entry_column):
                    return True

            return False
        
        textual_columns = []
        for column in columns:
            if column['type'] in ['title', 'text']:
                textual_columns.append(column['name'])
            
        text_filtered_response = []
        for entry in entries:
            keep_entry = True
            for column_name in textual_columns:
                if len(entry[column_name]) != 0 and len(entry[column_name]) <= 2:
                    keep_entry = False
                if contains_unwanted_content(entry[column_name]):
                    keep_entry = False
            if keep_entry:
                text_filtered_response.append(entry)

        return text_filtered_response

    def filter_select_cols(self, entries, columns):
        non_select_columns = []
        for column in columns:
            if not column['type'] in ['select', 'multi_select']:
                non_select_columns.append(column['name'])
 
        # change this filtering to check for non-text content
        filtered_entries = []
        for purchase in entries:
            num_empty = 0
            for column in non_select_columns:
                if purchase[column] == '':
                    num_empty += 1
            if num_empty <= int(len(columns)/2):
                filtered_entries.append(purchase)
        
        return filtered_entries

    def parse(self, filepath, columns, select_options = None):
        rekognition_response = self.get_rekognition_response(filepath)
        if 'Error' in rekognition_response:
            raise ReceiptParserError("invalid AWS response", include_name=False)

        parsed_response = self.parse_rekognition_response(rekognition_response, columns, select_options)
        if 'Error' in parsed_response:
            raise ReceiptParserError("invalid GPT response", include_name=False)

        return parsed_response
