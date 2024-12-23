# twitch2firestore-websocket-server

A websocket server that listens to Twitch chat messages and stores them in Firestore.

### Installation

First, install the required dependencies.

You can install the dependencies by running the following command in the root directory.

```bash
# start a virtual environment and install the dependencies
pip install -r requirements.txt

# or if you are using astral-sh/uv
uv run websocket.py
```



Create a .env file in the root directory and set up the environment variables.

```
# .env

# Twitch
TWITCH_CLIENT_ID = {YOUR_CLIENT_ID}
TWITCH_CLIENT_SECRET = {YOUR_CLIENT_SECRET}

# Firebase Project ID
PROJECT_ID = {YOUR_PROJECT_ID}
```


Download the service account key from Firebase and save it as `credentials.json` in the root directory.










Then start the server.

```python
python websocket.py
```

### Dependencies

-   requests
-   python-dotenv
-   asyncio
-   aiohttp
-   websockets
-   firebase_admin

