from dotenv import load_dotenv

class ReceiptParser:
    pass

prompt = """This list shows text extracted from a paper receipt. Return in JSON format the vendor where the purchase occurred, the product purchased, the date of purchase, and the cost of that service"""

from openai import OpenAI
import os

load_dotenv()

client = OpenAI(
    # This is the default and can be omitted
    api_key= os.getenv("API_KEY"),
)

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "how do you know everything",
        }
    ],
    model="gpt-3.5-turbo",
)

# chat completion object
completion_obj = chat_completion.choices[0].message

# get content
print(completion_obj.content)
