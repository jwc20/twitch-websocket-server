import json
from google.cloud import firestore
from datetime import datetime

import dotenv
import supabase

from pprint import pprint as pp

dotenv.load_dotenv()
channel_name = "sodapoppin"

db = firestore.Client.from_service_account_json("./credentials.json")

collection_ref = (
    db.collection("chats")
    .document(channel_name)
    .collection("2024")
    .document("12")
    .collection("24")
)
docs = collection_ref.stream()
data = [chat for doc in docs for chat in doc.to_dict().get("chats", [])]


pp(data)


