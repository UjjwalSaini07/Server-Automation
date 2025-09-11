import os
import sys
import signal
import multiprocessing
import logging
from dotenv import load_dotenv
from datetime import datetime
from zoneinfo import ZoneInfo

RUN_COUNT_FILE = ".server_run_count"
load_dotenv()
PERSIST_RUN_COUNT = os.getenv("PERSIST_RUN_COUNT", "false").lower() in ("1", "true", "yes")

# ---- services ----
from servers.server1.QuillixServerApi import start as start_api_ping
from servers.server2.stock_scraper import start as start_stock_scraper
from servers.server3.MVPserverApi import start as start_mvp_server

SERVICES = [
    ("Quillix API", start_api_ping, "API ping service started (All Week - IST 9:00 → 2:00)."),
    ("Stock Scraper", start_stock_scraper, "Stock scraper service started (Mon-Fri 9:30 → 16:00 IST)."),
    ("Affiliate MVP Health", start_mvp_server, "Affiliate health check service started (All Week - IST 9:00 → 2:00)."),
]

processes: list[multiprocessing.Process] = []

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

def get_run_count():
    """Return the run number. If persistence enabled, increment & store; otherwise always 1."""
    if PERSIST_RUN_COUNT:
        count = 0
        if os.path.exists(RUN_COUNT_FILE):
            try:
                with open(RUN_COUNT_FILE, "r") as f:
                    count = int(f.read().strip() or "0")
            except Exception:
                count = 0
        count += 1
        try:
            with open(RUN_COUNT_FILE, "w") as f:
                f.write(str(count))
        except Exception as e:
            logging.error(f"Unable to write run count file: {e}")
        return count
    else:
        return 1

def service_wrapper(name, target):
    """Wrap each service start() so KeyboardInterrupt and other errors are handled quietly."""
    try:
        target()
    except KeyboardInterrupt:
        logging.info(f"[{name}] received KeyboardInterrupt — exiting quietly")
    except SystemExit:
        logging.info(f"[{name}] exiting (SystemExit)")
    except Exception as e:
        logging.error(f"[{name}] exited with error: {e}")
    finally:
        return

# ---- start / shutdown ----
def start_services(run_number: int):
    ts = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S %Z")
    print("\n" + "-" * 6 + f" Server Running {run_number} " + "-" * 6)
    print(f"With Timestamp {ts}\n")

    for name, target, msg in SERVICES:
        p = multiprocessing.Process(target=service_wrapper, args=(name, target), name=name)
        p.start()
        processes.append(p)

        # ✅ Keep both logs
        logging.info(f"[Runner] Started service: {name} (PID {p.pid})")
        logging.info(f"Server : {msg}")

    print("\n")

def shutdown(signum=None, frame=None):
    ts = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S %Z")
    print(f"\n----Server is Terminated---- [{ts}]")

    for p in processes:
        if p.is_alive():
            try:
                logging.info(f"[Runner] Terminating {p.name} (PID {p.pid})...")
                p.terminate()
                p.join(timeout=5)
                if p.is_alive():
                    try:
                        p.kill()
                    except Exception:
                        pass
            except Exception as e:
                logging.error(f"[Runner] Error terminating {p.name}: {e}")

    logging.info("[Runner] All services stopped.")

    # Reset run counter if persistence is disabled
    if not PERSIST_RUN_COUNT and os.path.exists(RUN_COUNT_FILE):
        try:
            os.remove(RUN_COUNT_FILE)
        except Exception as e:
            logging.debug(f"Could not remove run count file: {e}")

    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    run_number = get_run_count()
    start_services(run_number)

    try:
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        shutdown()
