import json
from google.cloud import firestore
import datetime

db = firestore.Client.from_service_account_json("credentials.json")
collection_ref = db.collection('chats').document('sodapoppin').collection('2023').document('09').collection('02')
docs = collection_ref.stream()
data = [doc.to_dict() for doc in docs]

filename = 'chat_' + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M") + '.json'
with open(filename, 'w') as outfile:
    length = len(data)
    print("Number of hours recorded: ",length)
    json.dump(data, outfile)
    
    





