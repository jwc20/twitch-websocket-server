import os
import re
import asyncio
import aiohttp
import websockets
import signal
import json

import pandas as pd
import websockets
import re
import subprocess
from datetime import datetime

import spacy

nlp = spacy.load("en_core_web_sm")
import en_core_web_sm

nlp = en_core_web_sm.load()

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

import pytz

import secret_manager


# Use a service account. firebase
cred = credentials.Certificate("credentials.json")
app = firebase_admin.initialize_app(cred)
db = firestore.client()


project_id = "calm-armor-396402"
twitch_client_secret = "TWITCH_CLIENT_SECRET"
twitch_client_id = "TWITCH_CLIENT_ID"
# get secret key from secret_manager.py
CLIENT_ID, CLIENT_SECRET = secret_manager.twitch_get_secret(
    project_id, twitch_client_id, twitch_client_secret
)

# print(f"CLIENT_ID: {CLIENT_ID}, CLIENT_SECRET: {CLIENT_SECRET}")


# Twitch Configurations
# CHANNEL_NAME = "sodapoppin"
# CHANNEL_NAME = "zackrawrr"
CHANNEL_NAME = "summit1g"

# print(f"CLIENT_ID: {CLIENT_ID}, CLIENT_SECRET: {CLIENT_SECRET}")
print(f"CONNECTING TO: {CHANNEL_NAME}'s CHAT")

# Client Set for Websockets
clients = set()
chat_log = []


def remove_stopwords(sentence):
    """Remove stop words from a sentence"""
    doc = nlp(sentence)
    filtered_sentence = " ".join([token.text for token in doc if not token.is_stop])
    return filtered_sentence


# TODO: modify based on the result of the model
def preprocess_chat_message(sentence):
    sentence = re.sub(r"@\w+", "", sentence)
    sentence = sentence.lower()
    sentence = remove_stopwords(sentence)
    sentence = re.sub("[^a-zA-z0-9\s]", "", sentence)
    sentence = re.sub(r"\b(?!69\b|420\b)\d+\b", "", sentence)
    sentence = re.sub(r"\b\w{1,3}\b", "", sentence)
    sentence = re.sub(" +", " ", sentence).strip()
    return sentence


async def predict_toxicity(preprocessed_chat_message, model_path="model.vw"):
    """Predict the toxicity of a message using Vowpal Wabbit."""
    vw_formatted_message = f"|text {preprocessed_chat_message}"

    # Run VW for prediction
    result = subprocess.run(
        [
            "vw",
            "--quiet",
            "-i",
            model_path,
            "-t",
            "--predictions",
            "/dev/stdout",
            "--link",
            "logistic",
        ],
        input=vw_formatted_message.encode("utf-8"),
        capture_output=True,
    )

    # Parse the output to get prediction
    prediction = float(result.stdout.decode("utf-8").strip())
    return prediction


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
    # for client in clients:
    #     try:
    #         await client.send(message)
    #     except:
    #         continue


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
    print("Authenticated with Twitch")

    websocket_url = f"wss://irc-ws.chat.twitch.tv:443"
    while True:
        try:
            async with websockets.connect(websocket_url) as websocket:
                # print(websocket_url)

                # TODO change to get access token
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

                    # set timestamp1 to korean time zone

                    timestamp = datetime.now()
                    timestamp_isoformatted = timestamp.isoformat()
                    timestamp_formatted = timestamp.strftime("%H:%M:%S")

                    utcmoment_naive = datetime.utcnow()
                    utcmoment = utcmoment_naive.replace(tzinfo=pytz.utc)

                    # localFormat = "%Y-%m-%d %H:%M:%S"
                    # create an array with the korean timezone
                    koreaTime = pytz.timezone("Asia/Seoul")
                    # create a datetime object in korean timezone
                    koreaTimeNow = datetime.now(koreaTime)
                    # koreaTimeNow iso format
                    # koreaTimeNow_isoformatted = koreaTimeNow.isoformat()
                    # format the datetime object into a string
                    # koreaTimeNow_formatted  = koreaTimeNow_isoformatted.strftime(localFormat)

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
                    preprocessed_chat_message = preprocess_chat_message(chat_message)
                    vw_toxicity_score = await predict_toxicity(
                        preprocessed_chat_message
                    )  # => 1 not toxic | -1 toxic
                    toxicity_boolean = (
                        True if vw_toxicity_score < 0.5 else False
                    )  # this may need adjustment

                    # DO NOT ERASE THIS:
                    # year, month, day, hour = timestamp.strftime('%Y'), timestamp.strftime('%m'), timestamp.strftime('%d'), timestamp.strftime('%H')

                    # Need this for firestore timestamp
                    year, month, day, hour = (
                        koreaTimeNow.strftime("%Y"),
                        koreaTimeNow.strftime("%m"),
                        koreaTimeNow.strftime("%d"),
                        koreaTimeNow.strftime("%H"),
                    )

                    chat_dict = {
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

                    hour_document_ref = (
                        db.collection("chats")
                        .document(CHANNEL_NAME)
                        .collection(year)
                        .document(month)
                        .collection(day)
                        .document(hour)
                    )

                    formatted_message = (
                        f"[{timestamp_formatted}] <{username}> {chat_message}"
                    )

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


        except json.JSONDecodeError:
            print("Received data is not valid JSON.")

        except Exception as e:
            print(f"WebSocket Error: {e}")
            print("Reconnecting...")
            await asyncio.sleep(5)


def save_chat_log_to_json():
    now = datetime.now()
    formatted_date_time = now.strftime("%Y%m%d_%H%M")
    chat_log_filename = f"{CHANNEL_NAME}_chatlog_{formatted_date_time}.json"

    with open(chat_log_filename, "w") as file:
        json.dump(chat_log, file)


def shutdown_server(signum, frame):
    # save_chat_log_to_json()
    os._exit(0)


if __name__ == "__main__":
    # For local websocket server

    server = websockets.serve(ws_handler, "0.0.0.0", 8080) # Start WebSocket Server
    # server = websockets.serve(ws_handler, "127.0.0.1", 8080)
    # server = websockets.serve(ws_handler, "localhost", 5678)
    
    # start_server = websockets.serve(receive_chat_messages, "localhost", 8765)
    
    loop = asyncio.get_event_loop()
    loop.create_task(receive_chat_messages())  # Twitch Chat Receiver

    # register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, shutdown_server)
    signal.signal(signal.SIGTERM, shutdown_server)

    print("Websocket server address: ", server)
    loop.run_until_complete(server)
    loop.run_forever()
