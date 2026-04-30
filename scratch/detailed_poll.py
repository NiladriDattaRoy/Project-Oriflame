import requests
import time

url_login = 'https://project-oriflame-3.onrender.com/login'
url_fix = 'https://project-oriflame-3.onrender.com/oriflame-admin-panel-x9k2/fix_orphans'
creds = {'email': 'admin@oriflame.com', 'password': 'Admin123'} # Corrected password from earlier logs

s = requests.Session()
print(f"Attempting login to {url_login}...")
r_login = s.post(url_login, data=creds)
print(f"Login Response Status: {r_login.status_code}")
print(f"Final URL after login: {r_login.url}")

for i in range(10):
    print(f"Polling fix_orphans (attempt {i+1})...")
    r_fix = s.get(url_fix)
    print(f"Status: {r_fix.status_code}")
    if r_fix.status_code == 200:
        print("Success!")
        print("Response Text:", r_fix.text)
        break
    elif r_fix.status_code == 404:
        print("Not found yet - deployment might still be in progress.")
    else:
        print("Unexpected status code.")
    time.sleep(10)
