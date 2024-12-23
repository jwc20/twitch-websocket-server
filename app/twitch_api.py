# twitch_api.py
import aiohttp

class TwitchAPI:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret

    async def get_oauth_token(self):
        url = f"https://id.twitch.tv/oauth2/token?client_id={self.client_id}&client_secret={self.client_secret}&grant_type=client_credentials"
        async with aiohttp.ClientSession() as session:
            async with session.post(url) as response:
                data = await response.json()
                return data["access_token"]
