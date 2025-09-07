import time
import requests
import schedule
from datetime import datetime, timedelta, timezone
from pymongo import MongoClient, ASCENDING

API_URL = "https://nexgen-quillix.onrender.com/health"

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "Quillix-ServerAutomation"
COLLECTION_NAME = "api_health_logs"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

collection.create_index(
    [("expireAt", ASCENDING)],
    expireAfterSeconds=0
)

def ping_api():
    now = datetime.now(timezone.utc)
    expire_time = now + timedelta(hours=12)

    try:
        response = requests.get(API_URL, timeout=30)
        status = "SUCCESS" if response.status_code == 200 else f"FAILED: {response.status_code}"
        data = response.text if response.status_code == 200 else None

        print(f"[{now}] {status}")

        collection.insert_one({
            "timestamp": now,
            "status": status,
            "response": data,
            "expireAt": expire_time
        })

    except requests.exceptions.RequestException as e:
        print(f"[{now}] [ERROR] {e}")

        collection.insert_one({
            "timestamp": now,
            "status": "ERROR",
            "error": str(e),
            "expireAt": expire_time
        })

def main():
    schedule.every(2).minutes.do(ping_api)
    print(f"Started API keep-alive service for {API_URL}")

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()


# Todo: Using FireStore Server to Server
# import time
# import requests
# import schedule
# from datetime import datetime, timedelta, timezone
# import firebase_admin
# from firebase_admin import credentials, firestore

# API_URL = "https://nexgen-quillix.onrender.com/health"

# cred = credentials.Certificate("firebase_key.json")
# firebase_admin.initialize_app(cred)
# db = firestore.client()

# def ping_api():
#     now = datetime.now(timezone.utc)
#     expire_time = now + timedelta(hours=12)

#     try:
#         response = requests.get(API_URL, timeout=30)
#         status = "SUCCESS" if response.status_code == 200 else f"FAILED: {response.status_code}"
#         data = response.text if response.status_code == 200 else None

#         print(f"[{now}] {status}")

#         # Store in Firestore
#         doc_ref = db.collection("api_health_logs").document()
#         doc_ref.set({
#             "timestamp": now,
#             "status": status,
#             "response": data,
#             "expireAt": expire_time
#         })

#     except requests.exceptions.RequestException as e:
#         print(f"[{now}] [ERROR] {e}")

#         doc_ref = db.collection("api_health_logs").document()
#         doc_ref.set({
#             "timestamp": now,
#             "status": "ERROR",
#             "error": str(e),
#             "expireAt": expire_time
#         })

# def main():
#     schedule.every(5).minutes.do(ping_api)
#     print(f"Started API keep-alive service for {API_URL}")

#     while True:
#         schedule.run_pending()
#         time.sleep(1)

# if __name__ == "__main__":
#     main()
