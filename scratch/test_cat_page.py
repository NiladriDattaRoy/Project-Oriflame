import sys
sys.path.insert(0, '.')
from app import app

# Simulate what /category/makeup does
with app.test_client() as client:
    r = client.get('/category/makeup')
    print("Status:", r.status_code)
    data = r.get_data(as_text=True)
    # Find the error part
    if '500' in str(r.status_code) or 'Error' in data or 'Traceback' in data:
        print("Error found in response")
        # Print last part which might have traceback
        print(data[-3000:])
    else:
        print("OK - no error")
        print(data[:500])
