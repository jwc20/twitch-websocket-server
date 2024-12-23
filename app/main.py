# main.py
import os
import asyncio
import signal
from config import project_id, twitch_client_secret, twitch_client_id, CHANNEL_NAME
from chat_preprocessor import ChatPreprocessor
from toxicity_predictor import ToxicityPredictor
from twitch_api import TwitchAPI
from database_handler import DatabaseHandler
import websockets

# Instantiate the classes
chat_preprocessor = ChatPreprocessor()
toxicity_predictor = ToxicityPredictor()
twitch_api = TwitchAPI(twitch_client_id, twitch_client_secret)
database_handler = DatabaseHandler()

clients = set()
chat_log = []

async def receive_chat_messages():
    token = await twitch_api.get_oauth_token()
    print("Authenticated with Twitch")

    websocket_url = f"wss://irc-ws.chat.twitch.tv:443"
    while True:
        try:
            async with websockets.connect(websocket_url) as websocket:               
                await websocket.send(f"PASS oauth:{token}")
                await websocket.send(f"NICK justinfan123")  # for read-only
                await websocket.send(f"JOIN #{CHANNEL_NAME}")
                after_end_of_names = False
                while True:
                    message = await websocket.recv()
                    # ... (rest of the code for processing chat messages)
                    preprocessed_chat_message = chat_preprocessor.preprocess(chat_message)
                    vw_toxicity_score = await toxicity_predictor.predict(preprocessed_chat_message)
                    # ... (rest of the code for processing chat messages)
                    database_handler.update_chat(chat_dict, CHANNEL_NAME)

        except Exception as e:
            print(f"WebSocket Error: {e}")
            print("Reconnecting...")
            await asyncio.sleep(5)

def shutdown_server(signum, frame):
    # save_chat_log_to_json() (if required)
    os._exit(0)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(receive_chat_messages())  # Twitch Chat Receiver

    signal.signal(signal.SIGINT, shutdown_server)
    signal.signal(signal.SIGTERM, shutdown_server)

    loop.run_forever()
