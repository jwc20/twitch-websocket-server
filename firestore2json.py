import json
from google.cloud import firestore

# Initialize Firestore client with credentials
db = firestore.Client.from_service_account_json("credentials.json")

# Choose your Firestore collection
# collection_name = 'chat'
# collection_ref = db.collection(collection_name)
collection_ref = db.collection('chats').document('sodapoppin').collection('2023').document('08').collection('31')

# Fetch documents from the collection
docs = collection_ref.stream()

# Convert documents into a list of dictionaries
data = [doc.to_dict() for doc in docs]

# Export data to JSON file
with open(f'output.json', 'w') as outfile:
    # get length of list
    length = len(data)
    print(length)
    json.dump(data, outfile, indent=4)


