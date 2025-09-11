import os
import sys
import signal
import multiprocessing
from dotenv import load_dotenv

load_dotenv()

from servers.server1.QuillixServerApi import start as start_api_ping
from servers.server2.stock_scraper import start as start_stock_scraper
from servers.server3.MVPserverApi import start as start_mvp_server

# Registry of services
SERVICES = [
    ("Quillix API", start_api_ping),
    ("Stock Scraper", start_stock_scraper),
    ("Affiliate MVP Health", start_mvp_server),
]

# Keep track of processes
processes: list[multiprocessing.Process] = []

def start_services():
    """Start all registered services as separate processes."""
    print("\n")
    for name, target in SERVICES:
        p = multiprocessing.Process(target=target, name=name)
        p.start()
        processes.append(p)
        print(f"----Server is running----")
        print(f"[Runner] Started service: {name} (PID {p.pid})")
    print("\n")


def shutdown(signum=None, frame=None):
    """Gracefully terminate all child processes."""
    print("\n[Runner] Shutting down services...")
    for p in processes:
        if p.is_alive():
            print(f"[Runner] Terminating {p.name} (PID {p.pid})...")
            p.terminate()
            p.join(timeout=5)
    print("[Runner] All services stopped.")
    sys.exit(0)


if __name__ == "__main__":
    # Handle Ctrl+C / kill signals
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    print("[Runner] Starting all services...")
    start_services()

    try:
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        shutdown()
