import sys
import razorpay

key_id = 'rzp_live_SiC7yQ6wCHXpfb'
key_secret = 'hdAOiUwITZ4KgLsI0Nb6'

try:
    client = razorpay.Client(auth=(key_id, key_secret))
    order = client.order.create({
        'amount': 100, # 1 INR
        'currency': 'INR',
        'receipt': 'TEST1234'
    })
    print("Success! Order ID:", order['id'])
except Exception as e:
    print(f"ERROR: {e}")
