import os
import json

# Load configs for local hosting
path = 'config.json'
if os.path.isfile(path): # <-- file won't exist in production
  with open(path) as f: 
    config = json.loads(f.read())
  for key, value in config.items():
    os.environ[key] = value
  os.environ['test'] = '1'


from src.bot import run

print(r'''
  __  __               _____                  _ 
 |  \/  |             |  __ \                | |
 | \  / | __ _ _______| |__) |__ _  ___ ___  | |
 | |\/| |/ _` |_  / _ \  _  // _` |/ __/ _ \ | |
 | |  | | (_| |/ /  __/ | \ \ (_| | (_|  __/ |_|
 |_|  |_|\__,_/___\___|_|  \_\__,_|\___\___| (_)                                                                       
''')

# Run the bot
app = run()