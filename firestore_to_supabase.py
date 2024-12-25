import json
from google.cloud import firestore
from datetime import datetime
import os
import dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional


def initialize_firestore() -> firestore.Client:
    """Initialize and return Firestore client."""
    return firestore.Client.from_service_account_json("./credentials.json")


def get_postgres_connection():
    """Initialize and return PostgreSQL connection."""
    dotenv.load_dotenv()

    return psycopg2.connect(
        user=os.getenv("user"),
        password=os.getenv("password"),
        host=os.getenv("host"),
        port=os.getenv("port"),
        dbname=os.getenv("dbname")
    )


def create_chat_messages_table(cursor):
    """Create chat_messages table if it doesn't exist."""
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS chat_messages (
        chat_id TEXT PRIMARY KEY,
        chat_message TEXT NOT NULL,
        channel_name TEXT NOT NULL,
        username TEXT NOT NULL,
        timestamp TIMESTAMPTZ NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_chat_messages_timestamp 
    ON chat_messages(timestamp);

    CREATE INDEX IF NOT EXISTS idx_chat_messages_channel 
    ON chat_messages(channel_name);
    """
    cursor.execute(create_table_sql)


def get_chat_collection_ref(
        db: firestore.Client,
        channel_name: str,
        year: str,
        month: str,
        day: str
) -> firestore.CollectionReference:
    """Get reference to specific chat collection."""
    return (
        db.collection("chats")
        .document(channel_name)
        .collection(year)
        .document(month)
        .collection(day)
    )


def fetch_chat_data(collection_ref: firestore.CollectionReference) -> List[Dict[str, Any]]:
    """Fetch chat data from Firestore collection."""
    docs = collection_ref.stream()
    return [chat for doc in docs for chat in doc.to_dict().get("chats", [])]


def insert_chat_messages_to_postgres(
        cursor,
        chat_messages: List[Dict[str, Any]]
) -> None:
    """Insert chat messages into PostgreSQL."""
    insert_sql = """
    INSERT INTO chat_messages (chat_id, chat_message, channel_name, username, timestamp)
    VALUES (%(chat_id)s, %(chat_message)s, %(channel_name)s, %(username)s, %(timestamp)s)
    ON CONFLICT (chat_id) DO UPDATE SET
        chat_message = EXCLUDED.chat_message,
        channel_name = EXCLUDED.channel_name,
        username = EXCLUDED.username,
        timestamp = EXCLUDED.timestamp;
    """

    cursor.executemany(insert_sql, chat_messages)


def main():
    try:
        # Initialize Firestore
        db = initialize_firestore()

        # Initialize PostgreSQL connection
        conn = get_postgres_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Create table if it doesn't exist
        create_chat_messages_table(cursor)

        # Configure chat collection parameters
        channel_name = "sodapoppin"
        year, month, day = "2024", "12", "24"

        # Fetch chat data from Firestore
        collection_ref = get_chat_collection_ref(db, channel_name, year, month, day)
        chat_data = fetch_chat_data(collection_ref)

        # Insert chat messages to PostgreSQL
        insert_chat_messages_to_postgres(cursor, chat_data)

        # Commit the transaction
        conn.commit()
        print(f"Successfully inserted {len(chat_data)} messages")

    except Exception as e:
        print(f"An error occurred: {e}")
        conn.rollback()

    finally:
        # Close connections
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    main()