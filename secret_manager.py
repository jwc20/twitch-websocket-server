from dotenv import load_dotenv
import os

load_dotenv()

from google.cloud import secretmanager

credential_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")


def twitch_get_secret(
    project_id, twitch_client_id, twitch_client_secret, version_id="latest"
):
    client = secretmanager.SecretManagerServiceClient()
    client_secret = (
        f"projects/{project_id}/secrets/{twitch_client_secret}/versions/{version_id}"
    )
    client_id = (
        f"projects/{project_id}/secrets/{twitch_client_id}/versions/{version_id}"
    )
    response0 = client.access_secret_version(request={"name": client_id})
    response1 = client.access_secret_version(request={"name": client_secret})
    return response0.payload.data.decode("UTF-8"), response1.payload.data.decode(
        "UTF-8"
    )


# if __name__ == "__main__":
#     project_id = 'calm-armor-396402'
#     twitch_client_secret = 'TWITCH_CLIENT_SECRET'
#     twitch_client_id = 'TWITCH_CLIENT_ID'

#     secret_value = twitch_get_secret(project_id, twitch_client_id, twitch_client_secret)
#     print(secret_value)
