import requests
from bs4 import BeautifulSoup

url = "https://www.fashionphile.com/shop/hermes"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(url, headers=headers)

print("Status:", response.status_code)

soup = BeautifulSoup(response.text, "html.parser")

print(soup.title)