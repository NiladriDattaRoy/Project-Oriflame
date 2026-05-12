import requests
login_url = "https://project-oriflame-3.onrender.com/login"
credentials = {
    "email": "niladridattaroy25@gmail.com",
    "password": "Niladri@23",
    "remember": "on"
}

session = requests.Session()
response = session.post(login_url, data=credentials, allow_redirects=False)

print("Status Code:", response.status_code)
print("Headers:")
for k, v in response.headers.items():
    if k.lower() == 'set-cookie':
        print(f"Set-Cookie: {v}")
