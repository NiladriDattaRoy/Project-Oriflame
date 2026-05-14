
import os
from dotenv import load_dotenv
load_dotenv(override=True)
for k, v in os.environ.items():
    if 'DB' in k or 'DATABASE' in k or 'URL' in k:
        print(f"{k}: {v}")
