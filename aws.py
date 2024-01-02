import boto3
import json

def detect_text():
    session = boto3.Session(profile_name='default')
    client = session.client('rekognition')

    with open('receipt1.jpg', 'rb') as image_file:
        image_data = image_file.read()

    # call Amazon Rekognition API with ImageBytes parameter
    response = client.detect_text(Image={'Bytes': image_data})

    return response

data = detect_text()

with open('aws-sample-response2-alt.json', 'w') as file:
    json.dump(data, file, indent=4)