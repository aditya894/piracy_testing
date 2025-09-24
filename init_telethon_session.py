from decouple import config
from telethon import TelegramClient
import os

api_id = config("TG_API_ID", cast=int)
api_hash = config("TG_API_HASH")
session = config("TG_SESSION_FILE", default=".tg_session")

print("Using session file:", os.path.abspath(session))
client = TelegramClient(session, api_id, api_hash)
client.start()  # enter phone (+countrycode), code, and 2FA if set
print("Logged in. Saved to:", os.path.abspath(client.session.filename))
client.disconnect()
