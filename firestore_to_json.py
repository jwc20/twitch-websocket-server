import json
from google.cloud import firestore
from datetime import datetime

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


filename = channel_name + "_chat_" + datetime.now().strftime("%Y-%m-%d_%H-%M") + ".json"
with open(filename, "w") as outfile:
    length = len(data)
    json.dump(data, outfile, ensure_ascii=False)

    print(f"chats {length} recorder to {filename}")



