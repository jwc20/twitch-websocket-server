import json
from google.cloud import firestore
from datetime import datetime

channel_name = "sodapoppin"
db = firestore.Client.from_service_account_json("omfscene24-firebase-adminsdk-j15tw-d6d49b9999.json")
collection_ref = (
    db.collection("chats")
    .document(channel_name)
    .collection("2023")
    .document("09")
    .collection("03")
)
docs = collection_ref.stream()
data = [doc.to_dict() for doc in docs]

filename = channel_name + "_chat_" + datetime.now().strftime("%Y-%m-%d_%H-%M") + ".json"
with open(filename, "w") as outfile:
    length = len(data)
    print("Number of hours recorded: ", length)
    # json.dump(data[0]['chats'], outfile, indent=4)

    for i in range(length):
        json.dump(data[i]["chats"], outfile, indent=4)
        outfile.write("\n")
        print("Hour ", i + 1, " completed")
