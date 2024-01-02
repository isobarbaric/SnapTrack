from dotenv import load_dotenv
import json
from openai import OpenAI
import os

# loading api key
load_dotenv()

# initializing OpenAI client
client = OpenAI(api_key = os.getenv("API_KEY"))

# class ReceiptParser:
#     pass

def parse_receipt(aws_response):
    """Parses receipt and returns JSON dictionary 

    :param aws_response: a AWS Rekognition result
    :type aws_response: JSON dictionary
    :return: a list of items contained in the receipt
    :rtype: JSON dictionary
    """

    prompt = "This list shows text extracted from a paper receipt.\n"

    # clean up response to only include text content
    aws_response = [elem['DetectedText'] for elem in a['TextDetections']]

    # building a list of all of the text items on the receipt
    receipt_list = ""
    for item in aws_response:
        receipt_list += f"- {item}\n"

    prompt += receipt_list + "\nReturn in JSON format the vendor where each purchase occurred, the product purchased, the date of purchase, and the cost of that service. Do this for every single product on the receipt."

    gpt_response = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="gpt-3.5-turbo",
    )

    message = gpt_response.choices[0].message
    return json.loads(message.content)

# loading sample rekognition response to test parse_receipt
with open('aws-sample-response2.json', 'r') as f:
    a = json.load(f)
    
print(parse_receipt(a))