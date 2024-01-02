import json

with open('aws-sample-response.json', 'r') as f:
    a = json.load(f)

# remove everything other than text
print(a['TextDetections'][0])