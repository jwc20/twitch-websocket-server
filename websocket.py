import os
import re
import asyncio
import aiohttp
import websockets
import signal
import json


from datetime import datetime
# from collections import deque
from collections import namedtuple
from dotenv import load_dotenv


load_dotenv()

# Twitch Configurations
CLIENT_ID = os.environ.get("TWITCH_CLIENT_ID")
CLIENT_SECRET = os.environ.get("TWITCH_CLIENT_SECRET")
# CHANNEL_NAME = os.environ.get("TWITCH_CHANNEL_NAME")
CHANNEL_NAME = "summit1g"

print(
    f"CLIENT_ID: {CLIENT_ID}, CLIENT_SECRET: {CLIENT_SECRET}"
)


print(
    f"CONNECTING TO: {CHANNEL_NAME}'s CHAT"
)

# Client Set for Websockets
clients = set()

chat_log = []


async def get_oauth_token(client_id, client_secret):
    url = f"https://id.twitch.tv/oauth2/token?client_id={client_id}&client_secret={client_secret}&grant_type=client_credentials"
    async with aiohttp.ClientSession() as session:
        async with session.post(url) as response:
            data = await response.json()
            # print(data["access_token"])
            return data["access_token"]


async def forward_to_clients(message):
    for client in clients:
        try:
            await client.send(message)
        except:
            continue


async def register_client(websocket):
    clients.add(websocket)


async def unregister_client(websocket):
    clients.remove(websocket)


async def ws_handler(websocket, path):
    await register_client(websocket)
    try:
        async for message in websocket:
            await forward_to_clients(message)
    except:
        pass
    finally:
        await unregister_client(websocket)


async def receive_chat_messages():
    token = await get_oauth_token(CLIENT_ID, CLIENT_SECRET)
    websocket_url = f"wss://irc-ws.chat.twitch.tv:443"
    while True:
        try:
            async with websockets.connect(websocket_url) as websocket:
                print(websocket_url)
                await websocket.send(f"PASS oauth:{token}")
                await websocket.send(f"NICK justinfan123")  # for read-only
                await websocket.send(f"JOIN #{CHANNEL_NAME}")
                after_end_of_names = False
                while True:
                    
                    # TODO: Check for stream start message.
                    
                    message = await websocket.recv()
                    message = message.strip().replace("\n", "")
                    if not after_end_of_names:
                        match = re.search(r":End of /NAMES list", message)
                        if match:
                            after_end_of_names = True
                        continue
                    

                    # Extracting chat messages for forwarding
                    match_nick = re.search(r"@(\w+)\.tmi\.twitch\.tv", message)
                    match_chat = re.search(r"PRIVMSG #\w+ :(.*)", message)
                    
                    timestamp = datetime.now()
                    timestamp_isoformatted = timestamp.isoformat()
                    timestamp_formatted = timestamp.strftime("%H:%M:%S")
                    
                    username = match_nick.group(1) if match_nick else ""
                    chat_message = match_chat.group(1) if match_chat else ""

                    formatted_message = f"[{timestamp_formatted}] <{username}> {chat_message}"
                    print(formatted_message)

                    chat_dict = {"username": username, "chat_message": chat_message, "timestamp": timestamp_isoformatted}
                    chat_log.append(chat_dict)

                    await forward_to_clients(formatted_message)
                    
        except Exception as e:
            print(f"WebSocket Error: {e}")
            print("Reconnecting...")
            await asyncio.sleep(5)


def save_chat_log_to_json():
    with open('chat_log.json', 'w') as file:
        json.dump(chat_log, file)


def shutdown_server(signum, frame):
    save_chat_log_to_json()
    os._exit(0)

    
if __name__ == "__main__":
    # For local websocket server
    loop = asyncio.get_event_loop()
    loop.create_task(receive_chat_messages())  # Twitch Chat Receiver
    # server = websockets.serve(ws_handler, "0.0.0.0", 8080) # Start WebSocket Server
    server = websockets.serve(ws_handler, "127.0.0.1", 8080)  
    # server = websockets.serve(ws_handler, "localhost", 5678)

    # register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, shutdown_server)
    signal.signal(signal.SIGTERM, shutdown_server)

    print("Websocket server address: ", server)
    loop.run_until_complete(server)
    loop.run_forever()

