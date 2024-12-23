import secret_manager 

project_id = "calm-armor-396402"
twitch_client_secret = "TWITCH_CLIENT_SECRET"
twitch_client_id = "TWITCH_CLIENT_ID"
CLIENT_ID, CLIENT_SECRET = secret_manager.twitch_get_secret(
    project_id, twitch_client_id, twitch_client_secret
)
CHANNEL_NAME = "avoidingthepuddle"
# CHANNEL_NAME = "sodapoppin"

