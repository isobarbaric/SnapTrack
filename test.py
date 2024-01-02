import json

from receipt_parser import ReceiptParser

a = ReceiptParser()
data = a.parse('receipt2.jpg')

with open('aws-sample-response2-alt.json', 'w') as file:
    json.dump(data, file, indent=4)    
