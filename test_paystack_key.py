import os
import requests
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")

url = "https://api.paystack.co/balance"
headers = {
    "Authorization": f"Bearer {SECRET_KEY}",
    "Content-Type": "application/json"
}

response = requests.get(url, headers=headers)
print("Status Code:", response.status_code)
print("Response JSON:", response.json())
