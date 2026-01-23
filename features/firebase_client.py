import os
import json
import firebase_admin
from firebase_admin import credentials, db, get_app
from dotenv import load_dotenv

load_dotenv()

def init_firebase():
    try:
        return get_app()
    except ValueError:
        pass

    db_url = os.getenv("FIREBASE_DB_URL")
    sa_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")

    if not db_url:
        raise RuntimeError("FIREBASE_DB_URL missing")
    if not sa_json:
        raise RuntimeError("FIREBASE_SERVICE_ACCOUNT_JSON missing")

    try:
        sa_dict = json.loads(sa_json)
    except json.JSONDecodeError as e:
        raise RuntimeError("Invalid FIREBASE_SERVICE_ACCOUNT_JSON format") from e

    cred = credentials.Certificate(sa_dict)

    return firebase_admin.initialize_app(cred, {"databaseURL": db_url})

def get_ref(path: str):
    init_firebase()
    return db.reference(path)