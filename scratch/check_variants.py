import requests
import re

html = requests.get('https://project-oriflame-3.onrender.com/products/the-one-smart-sync-lipstick').text
match = re.search(r'<div class="product-variants">(.*?)</div>\s*</div>', html, re.DOTALL)
if match:
    print(match.group(0))
else:
    print("No match")
