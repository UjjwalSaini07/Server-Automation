import os
import multiprocessing
from dotenv import load_dotenv

load_dotenv()

from servers.server1.api_ping import start as start_api_ping
from servers.server2.stock_scraper import start as start_stock_scraper

if __name__ == "__main__":
    p1 = multiprocessing.Process(target=start_api_ping)
    p2 = multiprocessing.Process(target=start_stock_scraper)

    p1.start()
    p2.start()

    p1.join()
    p2.join()
