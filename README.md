# twitch-websocket-server

First, install the required dependencies.

```bash
pip install -r requirements.txt
```

Create a .env file and set up the environment variables.

```
# .env

TWITCH_CLIENT_ID = {YOUR_CLIENT_ID}
TWITCH_CLIENT_SECRET = {YOUR_CLIENT_SECRET}
TWITCH_CHANNEL_NAME = {CHANNEL_NAME}
```

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
