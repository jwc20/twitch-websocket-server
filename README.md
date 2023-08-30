# twitch-websocket-server

First, install the required dependencies.

```bash
pip install -r requirements.txt
```

Install [spacy](https://spacy.io/usage)

```bash
pip install -U pip setuptools wheel
pip install -U spacy # pip install -U 'spacy[apple]' for Mac M1
python -m spacy download en_core_web_sm
```

Create a .env file in the root directory and set up the environment variables.

```
# .env
TWITCH_CLIENT_ID = {YOUR_CLIENT_ID}
TWITCH_CLIENT_SECRET = {YOUR_CLIENT_SECRET}
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
-   firebase_admin
-   pandas
-   spacy

### Other tools

- Vowpal Wabbit
