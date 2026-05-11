import sys
sys.path.insert(0, '.')
from app import app

cats = ['makeup','fragrance','hair-care','bath-and-body','personal-care','wellness','accessories','mens-care','gift-sets','skincare']

with app.test_client() as client:
    for cat in cats:
        r = client.get(f'/category/{cat}')
        status = 'OK' if r.status_code == 200 else 'FAIL'
        print(f'[{status}] {r.status_code} /category/{cat}')
