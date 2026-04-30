import time
import requests

s = requests.Session()
s.post('https://project-oriflame-3.onrender.com/login', data={'email':'admin@oriflame.com', 'password':'admin123'})

print("Polling...")
for _ in range(30):
    r = s.get('https://project-oriflame-3.onrender.com/oriflame-admin-panel-x9k2/fix_orphans')
    if r.status_code == 200:
        print("SUCCESS:", r.text)
        break
    time.sleep(5)
print("Done")
