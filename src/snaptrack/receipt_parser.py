import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import json
from openai import OpenAI
import os

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

        prompt = f"Train: You are an expert in exploratory data extraction. You have award-winning proficiency in identifying and collecting relevant information from the text extracted from paper receipts. Based on your extensive experience and expertise, analyze a receipt's text list. There are labels that represent columns in a Notion database. Scrutinize all extracted text for each entry in the receipt and assign them to appropriate labels. Some of the columns of the database are of type 'Select' and type 'Multi-select' and hence have associated categories. For such columns, please do not mix categories defined within one label with another. For a particular product, assign a label an empty string if you are unsure what value should be assigned, but make sure to ALWAYS include every label for a particular entry. Please include dates in %Y/%m/%d format excluding time, and correct the content in a title word format. Your output should ONLY be a list of JSON objects and nothing else. This list is text extracted from a paper receipt: "

        # clean up response to only include text content
        aws_response = [elem['DetectedText'] for elem in aws_response['TextDetections']]

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

        print(prompt)

        # passing prompt to GPT-3.5 and gettings its response
        gpt_response = openai_client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="gpt-4"
        )

        message = gpt_response.choices[0].message
        print(message)

        try:
            details = json.loads(message.content)
        except json.decoder.JSONDecodeError as e:
            details = {'Error': e}

        return details

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
