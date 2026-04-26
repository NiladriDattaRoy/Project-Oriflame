import requests

try:
    s = requests.Session()
    # Let's bypass login or just login if we can.
    # Since we can't easily, let's just make a script to parse the flask log.
    pass
except Exception as e:
    print(e)
