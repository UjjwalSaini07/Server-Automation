# main.py
import time
import requests
import schedule
from datetime import datetime, timedelta

import firebase_admin
from firebase_admin import credentials, firestore

API_URL = "https://nexgen-quillix.onrender.com/health"

# Initialize Firebase
cred = credentials.Certificate("firebase_key.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

def ping_api():
    try:
        response = requests.get(API_URL, timeout=30)
        status = "SUCCESS" if response.status_code == 200 else f"FAILED: {response.status_code}"
        data = response.text if response.status_code == 200 else None
        print(f"[{datetime.utcnow()}] {status}")

        # Store in Firestore with TTL (12 hours)
        doc_ref = db.collection("api_health_logs").document()
        expire_time = datetime.utcnow() + timedelta(hours=12)

        doc_ref.set({
            "timestamp": datetime.utcnow(),
            "status": status,
            "response": data,
            "expireAt": expire_time  # Firestore TTL field
        })

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to reach API: {e}")
        # Still log the error
        doc_ref = db.collection("api_health_logs").document()
        expire_time = datetime.utcnow() + timedelta(hours=12)

        doc_ref.set({
            "timestamp": datetime.utcnow(),
            "status": "ERROR",
            "error": str(e),
            "expireAt": expire_time
        })

def main():
    # Schedule the API call every 5 minutes
    schedule.every(5).minutes.do(ping_api)
    print(f"Started API keep-alive service for {API_URL}")

    # Run forever
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
