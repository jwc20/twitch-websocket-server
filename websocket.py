import os
import re
import asyncio
import aiohttp
import websockets
import signal
import json
import hashlib
from datetime import datetime
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# Firebase setup
cred = credentials.Certificate("./credentials.json")
app = firebase_admin.initialize_app(cred)
db = firestore.client()

# Load environment variables
load_dotenv()
PROJECT_ID = os.getenv("PROJECT_ID")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")

# Twitch Configurations
CHANNEL_NAME = "sodapoppin"
print(f"CONNECTING TO: {CHANNEL_NAME}'s CHAT")

# Client Set for Websockets
clients = set()
chat_log = []


async def get_oauth_token(client_id, client_secret):
    url = f"https://id.twitch.tv/oauth2/token?client_id={client_id}&client_secret={client_secret}&grant_type=client_credentials"
    async with aiohttp.ClientSession() as session:
        async with session.post(url) as response:
            data = await response.json()
            return data["access_token"]


async def forward_to_clients(message):
    if clients:
        tasks = [client.send(message) for client in clients]
        await asyncio.gather(*tasks)


async def register_client(websocket):
    clients.add(websocket)


async def unregister_client(websocket):
    clients.remove(websocket)


async def ws_handler(websocket, path):
    await register_client(websocket)
    try:
        async for message in websocket:
            await forward_to_clients(message)
    finally:
        await unregister_client(websocket)


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
                    if not after_end_of_names:
                        match = re.search(r":End of /NAMES list", message)
                        if match:
                            after_end_of_names = True
                        continue

                    match_nick = re.search(r"@(\w+)\.tmi\.twitch\.tv", message)
                    match_chat = re.search(r"PRIVMSG #\w+ :(.*)", message)

                    timestamp = datetime.utcnow()
                    timestamp_isoformatted = timestamp.isoformat()
                    timestamp_formatted = timestamp.strftime("%H:%M:%S")

                    remove_list = [
                        "Fossabot",
                        "Nightbot",
                        "StreamElements",
                        "Streamlabs",
                        "OkayegBOT",
                    ]
                    username = match_nick.group(1) if match_nick else ""

                    if any(x in username for x in remove_list):
                        continue

                    chat_message = match_chat.group(1) if match_chat else ""

                    # Note: These functions need to be implemented or removed
                    # preprocessed_chat_message = preprocess_chat_message(chat_message)
                    # vw_toxicity_score = await predict_toxicity(preprocessed_chat_message)
                    preprocessed_chat_message = chat_message  # Temporary placeholder
                    vw_toxicity_score = 1.0  # Temporary placeholder

                    toxicity_boolean = True if vw_toxicity_score < 0.5 else False

                    year, month, day, hour = timestamp.strftime('%Y'), timestamp.strftime('%m'), timestamp.strftime(
                        '%d'), timestamp.strftime('%H')

                    hour_document_ref = (
                        db.collection("chats")
                        .document(CHANNEL_NAME)
                        .collection(year)
                        .document(month)
                        .collection(day)
                        .document(hour)
                    )

                    hash = hashlib.sha256(message.encode('utf-8')).hexdigest()

                    chat_dict = {
                        "chat_id": hash,
                        "username": username,
                        "chat_message": chat_message,
                        "preprocessed_chat_message": preprocessed_chat_message,
                        "timestamp": timestamp_isoformatted,
                        "vw_toxicity_score": vw_toxicity_score,
                        "is_toxic": toxicity_boolean,
                        "channel_name": CHANNEL_NAME,
                        "last_labeler": "",
                        "last_label_timestamp": "",
                        "labeler_list": [],
                    }

                    chat_log.append(chat_dict)

                    formatted_message = f"[{timestamp_formatted}] <{username}> {chat_message}"
                    print(formatted_message)
                    await forward_to_clients(json.dumps(chat_dict))

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


def save_chat_log_to_json():
    now = datetime.now()
    formatted_date_time = now.strftime("%Y%m%d_%H%M")
    chat_log_filename = f"{CHANNEL_NAME}_chatlog_{formatted_date_time}.json"
    with open(chat_log_filename, "w") as file:
        json.dump(chat_log, file)


async def main():
    # Start the websocket server
    server = await websockets.serve(ws_handler, "0.0.0.0", 8080)

    # Start the chat message receiver
    await receive_chat_messages()

    # Keep the server running
    await server.wait_closed()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down...")
        save_chat_log_to_json()