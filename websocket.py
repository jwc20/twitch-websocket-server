import os
import re
import asyncio
import aiohttp
import websockets
import json
import hashlib
from datetime import datetime, UTC
from dotenv import load_dotenv

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# Firebase setup
cred = credentials.Certificate("./credentials.json")
app = firebase_admin.initialize_app(cred)
db = firestore.client()

# Load environment variables from .env file
load_dotenv()
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")

# Twitch Configurations
CHANNEL_NAME = "sodapoppin"
print(f"CONNECTING TO: {CHANNEL_NAME}'s CHAT")


async def get_oauth_token(client_id, client_secret):
    url = f"https://id.twitch.tv/oauth2/token?client_id={client_id}&client_secret={client_secret}&grant_type=client_credentials"
    async with aiohttp.ClientSession() as session:
        async with session.post(url) as response:
            data = await response.json()
            return data["access_token"]


async def receive_chat_messages():
    token = await get_oauth_token(TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET)
    print("Authenticated with Twitch")

    websocket_url = "wss://irc-ws.chat.twitch.tv:443"
    while True:
        try:
            async with websockets.connect(websocket_url) as websocket:
                print(websocket_url)

                await websocket.send(f"PASS oauth:{token}")
                await websocket.send("NICK justinfan123")  # for read-only
                await websocket.send(f"JOIN #{CHANNEL_NAME}")

                after_end_of_names = False
                while True:
                    message = await websocket.recv()
                    message = message.strip().replace("\n", "")
                    hash = hashlib.sha256(message.encode("utf-8")).hexdigest()

                    if not after_end_of_names:
                        match = re.search(r":End of /NAMES list", message)
                        if match:
                            after_end_of_names = True
                        continue

                    match_nick = re.search(r"@(\w+)\.tmi\.twitch\.tv", message)
                    match_chat = re.search(r"PRIVMSG #\w+ :(.*)", message)

                    username = match_nick.group(1) if match_nick else ""
                    chat_message = match_chat.group(1) if match_chat else ""

                    timestamp = datetime.now(UTC)
                    timestamp_iso_formatted = timestamp.isoformat()
                    year, month, day, hour = (
                        timestamp.strftime("%Y"),
                        timestamp.strftime("%m"),
                        timestamp.strftime("%d"),
                        timestamp.strftime("%H"),
                    )

                    # formatted_message = f"[{timestamp_formatted}] <{username}> {chat_message}"
                    # print(formatted_message)

                    hour_document_ref = (
                        db.collection("chats")
                        .document(CHANNEL_NAME)
                        .collection(year)
                        .document(month)
                        .collection(day)
                        .document(hour)
                    )

                    chat_dict = {
                        "chat_id": hash,
                        "username": username,
                        "chat_message": chat_message,
                        "timestamp": timestamp_iso_formatted,
                        "channel_name": CHANNEL_NAME,
                    }

                    if hour_document_ref.get().exists:
                        hour_document_ref.update(
                            {"chats": firestore.ArrayUnion([chat_dict])}
                        )
                    else:
                        hour_document_ref.set(
                            {"chats": firestore.ArrayUnion([chat_dict])}
                        )

        except websockets.exceptions.ConnectionClosed:
            print("Connection closed. Reconnecting...")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"Error: {e}")
            print("Reconnecting...")
            await asyncio.sleep(5)


async def main():
    await receive_chat_messages()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down...")
