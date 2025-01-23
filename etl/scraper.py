import asyncio
import os
import shutil
from datetime import datetime, timedelta
from typing import List

from dotenv import load_dotenv

load_dotenv()


async def scrape_unikon_event_list(url: str):
    pass


async def scrape_brite_event_list(url: str):
    pass


async def scrape_crossweb_articles_event_list(url: str):
    pass


async def main():
    tasks = []
    for url in URLS:
        if "nikonferencje" in url:
            tasks.append(asyncio.create_task(scrape_unikon_event_list(url)))
        elif "eventbrite" in url:
            tasks.append(asyncio.create_task(scrape_brite_event_list(url)))
        elif "crossweb" in url:
            tasks.append(asyncio.create_task(scrape_crossweb_articles_event_list(url)))

    await asyncio.gather(*tasks)


def clear_output_dir():
    output_dir: str = os.getenv("SCRAPING_OUTPUT_DIR")
    if os.path.exists(output_dir):
        print("Removing existing output directory")
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)


if __name__ == "__main__":
    try:
        with open("last_update_timestamp.txt", "r") as f:
            last_update_timestamp: str = f.read().strip()
            last_update_timestamp = datetime.strptime(last_update_timestamp, "%d-%m-%Y %H:%M")
    except FileNotFoundError:
        last_update_timestamp = None  # If the file doesn't exist, set to None

    if last_update_timestamp is None or datetime.now() - last_update_timestamp > timedelta(hours=12):
        clear_output_dir()
        URLS: List[str] = os.getenv("SCRAPING_URLS").split(",")
        asyncio.run(main())

        # Update the last update timestamp
        with open("last_update_timestamp.txt", "w") as f:
            f.write(datetime.now().strftime("%d-%m-%Y %H:%M"))
    else:
        print("Last update was less than 12 hours ago. Skipping scraping.")
