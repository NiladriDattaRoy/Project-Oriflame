import requests, re
r = requests.get('https://project-oriflame-3.onrender.com/')
matches = re.findall("Nilu.s Oriflame", r.text)
print("Occurrences on live homepage:", len(matches))
print("Samples:", matches[:3])
