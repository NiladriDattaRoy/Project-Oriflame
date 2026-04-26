import requests
try:
    r = requests.get('https://project-oriflame.onrender.com/')
    print(r.status_code)
    print(r.text[:500])
except Exception as e:
    print("Error:", e)
