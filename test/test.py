import json
from snaptrack.receipt_parser import ReceiptParser

a = ReceiptParser()
data = a.parse(filepath='../data/receipts/receipt2.jpg')

with open('../data/purchase-data.json', 'w') as file:
    json.dump(data, file, indent=4)    
