import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import json
from openai import OpenAI
import os
import time

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

    def parse_rekognition_response(self, aws_response, categories, select_options = None):
        """Parses receipt and returns JSON dictionary 

        :param aws_response: a AWS Rekognition result
        :type aws_response: JSON dictionary
        :param categories: a list of categories to parse for, stuctured as {column_name: column_type}
        :type categories: list of dictionaries
        :return: a list of items contained in the receipt
        :rtype: JSON dictionary
        """
        # clean up response to only include text content
        aws_text = [elem['DetectedText'] for elem in aws_response['TextDetections']]

        # building a list of all of the text items on the receipt
        receipt_list = "["
        for item in aws_text[:-1]:
            receipt_list += f"{item}, "
        receipt_list += f"{aws_text[-1]}]"
        
        # print(prompt)
        # passing prompt to GPT-3.5 and gettings its response
        purchases = self.process_non_select_cols(receipt_list, categories)

        select_column_names = select_options.keys()
        print(purchases)

        # loop through individual select columns and add key to each page
        # code here

        return purchases

    def get_gpt_response(self, prompt):
        gpt_response = openai_client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="gpt-3.5-turbo"
        )

        message = gpt_response.choices[0].message
        # print(message)

        try:
            # details = json.loads(message)
            details = json.loads(message.content)
        except json.decoder.JSONDecodeError as e:
            details = {'Error': e}

        return details

    def process_non_select_cols(self, receipt_list, categories):
        # created a detailed prompt for task
        prompt = "There are labels that represent columns in a Notion database. Scrutinize all extracted text for each entry in the receipt and assign them to appropriate labels (don't create your own labels, only create keys for given labels). For a particular product, assign a label an empty string if you are unsure what value should be assigned, but make sure to ALWAYS include every label for a particular entry. Please include dates in %Y/%m/%d format excluding time, and correct the content in a title word format. Note that each entry will have the same date that should be a part of the receipt. Your output should ONLY be a list of JSON objects and nothing else. Don't list payment details, vendor details as separate purchases. This list is text extracted from a paper receipt: "

        # adding items on receipt to prompt
        prompt += receipt_list

        columns = ''
        for column in categories:
            if column['type'] in ['select', 'multi_select']:
                continue
            columns += f"\n- {column['name']} "

        prompt += columns
        # print(prompt)

        # remove those with empty 
        # count length
        # sort, choose elem with minimum length

        batches = []
        for i in range(1, 4):
            # processing one batch of responses
            # print(f'Batch #{i}')
            current_batch = []

            try:
                gpt_json = self.get_gpt_response(prompt)
            except Exception as e:
                pass

            for entry in gpt_json:
                curr_entry = 0
                for key, value in entry.items():
                    if value == '':
                        curr_entry += 1
                if curr_entry <= int(len(categories)/2):
                    current_batch.append(entry)
            
            batches.append([len(current_batch), current_batch])
            # print(batches[-1])
            # print('\n')
            time.sleep(1)
    
        # print(batches)

        # batches.sort()
        min_batch_size = 100000
        best_batch = None
        for batch in batches:
            if batch[0] < min_batch_size:
                min_batch_size = batch[0]
                best_batch = batch[1]
        
        # remove lists with empty length from batches.append
        # first figure out why getting zero length

        # choose between similar length lists

        return best_batch
 
    def process_select_columns(self, aws_response, categories, select_options = None):
        prompt = "Some of the columns of the database are of type 'Select' and type 'Multi-select' and hence have associated categories. For such columns, please do not mix categories defined within one label with another."

        # building a list of all of the text items on the receipt
        receipt_list = "["
        for item in aws_response[:-1]:
            receipt_list += f"{item}, "
        receipt_list += f"{aws_response[-1]}]"

        # adding additional info to prompt
        # TODO: clean up code
        criteria = ''
        for column in categories:
            criteria += f"\n- {column['name']} "
            if column['type'] == 'select':
                criteria += "(this is a column of type 'Select' and you can choose upto one of the following options; you can keep your selection empty in case no suitable category is available:  " + ''.join([f'{option}, ' for option in select_options[column['name']]][:-1]) 
                
                if len(select_options[column['name']]) > 1:
                    criteria += select_options[column['name']][-1] + ')'
                else:
                    criteria += ')'
            elif column['type'] == 'multi_select':
                criteria += "(this is a column of type 'Multi-select' and you can choose multiple of the following categories (return your selection as a list); you can keep your selection empty in case no suitable categories are available: " + ''.join([f'{option}, ' for option in select_options[column['name']]][:-1])

                if len(select_options[column['name']]) > 1:
                    criteria += select_options[column['name']][-1] + ')'
                else:
                    criteria += ')'
        
        prompt += receipt_list + f"\nYour labels are {criteria}"

    def parse(self, filepath, categories, select_options):
        rekognition_response = self.get_rekognition_response(filepath)
        if 'Error' in rekognition_response:
            # raise ReceiptParserError(rekognition_response['Error'])
            # separate issue, change description

            # print(parsed_response['Error'])
            raise ReceiptParserError("Invalid AWS response", include_name=False)

        parsed_response = self.parse_rekognition_response(rekognition_response, categories, select_options)
        if 'Error' in parsed_response:
            # raise ReceiptParserError(parsed_response['Error'])
            # str: Expecting value: line 1 column 1 (char 0)
            # separate issue, change description

            # print(parsed_response['Error'])
            # "GPT unable to parse AWS response"
            raise ReceiptParserError("invalid GPT response", include_name=False)

        return parsed_response
