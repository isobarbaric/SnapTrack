import boto3
from dotenv import load_dotenv
import json
from openai import OpenAI
import os

# loading api key
load_dotenv()

# initializing OpenAI client
openai_client = OpenAI(api_key = os.getenv("API_KEY"))

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
        session = boto3.Session(profile_name='default')
        aws_client = session.client('rekognition')

        with open(filepath, 'rb') as image_file:
            image_data = image_file.read()

        # call Amazon Rekognition API
        response = aws_client.detect_text(Image={'Bytes': image_data})

        return response

    def parse_rekognition_response(self, aws_response):
        """Parses receipt and returns JSON dictionary 

        :param aws_response: a AWS Rekognition result
        :type aws_response: JSON dictionary
        :return: a list of items contained in the receipt
        :rtype: JSON dictionary
        """

        prompt = "This list shows text extracted from a paper receipt.\n"

        # clean up response to only include text content
        aws_response = [elem['DetectedText'] for elem in aws_response['TextDetections']]

        # building a list of all of the text items on the receipt
        receipt_list = ""
        for item in aws_response:
            receipt_list += f"- {item}\n"

        # adding additional info to prompt
        prompt += receipt_list + "\nReturn in JSON format the vendor where each purchase occurred, the product purchased, the date of purchase, and the cost of that service. Do this for every single product on the receipt, and the format should be a list of such JSON objects."

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

        print(gpt_response)

        message = gpt_response.choices[0].message
        return json.loads(message.content)

    def parse(self, filepath):
        rekognition_response = self.get_rekognition_response(filepath)
        return self.parse_rekognition_response(rekognition_response)
    
