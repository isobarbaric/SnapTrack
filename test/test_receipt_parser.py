import json
from snaptrack.receipt_parser import ReceiptParser

a = ReceiptParser()
data = a.parse(filepath='../data/receipts/receipt1.jpg', categories=['Date', 'Place', 'What', 'Amount'])

with open('../data/purchase-data.json', 'w') as file:
    json.dump(data, file, indent=4)    
