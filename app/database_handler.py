# database_handler.py
import pytz
from datetime import datetime
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

class DatabaseHandler:
    def __init__(self):
        # Use a service account for firebase
        cred = credentials.Certificate("../credentials.json")
        app = firebase_admin.initialize_app(cred)
        self.db = firestore.client()

    def get_korean_timestamp(self):
        koreaTime = pytz.timezone("Asia/Seoul")
        koreaTimeNow = datetime.now(koreaTime)
        return koreaTimeNow

    def update_chat(self, chat_dict, channel_name):
        koreaTimeNow = self.get_korean_timestamp()
        year, month, day, hour = (
            koreaTimeNow.strftime("%Y"),
            koreaTimeNow.strftime("%m"),
            koreaTimeNow.strftime("%d"),
            koreaTimeNow.strftime("%H"),
        )

        hour_document_ref = (
            self.db.collection("chats")
            .document(channel_name)
            .collection(year)
            .document(month)
            .collection(day)
            .document(hour)
        )

        if hour_document_ref.get().exists:
            hour_document_ref.update(
                {"chats": firestore.ArrayUnion([chat_dict])}
            )
        else:
            hour_document_ref.set(
                {"chats": firestore.ArrayUnion([chat_dict])}
            )
