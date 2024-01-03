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
    def __init__(self, message):
        self.message = message 
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

        prompt = "This list is text extracted from a paper receipt: "

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
                criteria += "(this field is a selection field and you must choose one the following options: " + ''.join([f'{option}, ' for option in select_options[column['name']]][:-1]) + select_options[column['name']][-1] + ')'
            elif column['type'] == 'multi_select':
                criteria += "(this field is a multi-selection field and you must choose one or more of the following options: " + ''.join([f'{option}, ' for option in select_options[column['name']]][:-1]) + select_options[column['name']][-1] + ')'
        
        prompt += receipt_list + f"\nReturn in JSON format the following information about each of the products on the receipt: {criteria}\nDo this for every single product on the receipt, and the format should be a list of such JSON objects (ensure the keys have the right spelling and case)."

        # print(prompt)

        # passing prompt to GPT-3.5 and gettings its response
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
            details = json.loads(message.content)
        except json.decoder.JSONDecodeError as e:
            details = {'Error': str(e)}

        return details

    def parse(self, filepath, categories, select_options):
        rekognition_response = self.get_rekognition_response(filepath)
        if 'Error' in rekognition_response:
            raise ReceiptParserError(rekognition_response['Error'])

        parsed_response = self.parse_rekognition_response(rekognition_response, categories, select_options)
        if 'Error' in parsed_response:
            raise ReceiptParserError(parsed_response['Error'])

        return parsed_response
