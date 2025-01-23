import asyncio
import os
import shutil
from datetime import datetime, timedelta
from typing import List

import backoff
import requests
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()


async def scrape_unikon_events(url: str):
    pass


async def scrape_brite_events(url: str):
    pass


async def scrape_crossweb_events(url: str):
    with requests.get(url) as response:
        response.raise_for_status()
        response_text = response.text
        event_list_soup = BeautifulSoup(response_text, "html.parser")
    event_urls: List[str] = [
        anchor["href"] for anchor in event_list_soup.find_all("a", class_="clearfix")
    ]
    print(f"Found {len(event_urls)} events on Crossweb")

    tasks = []
    for event_url in event_urls:
        tasks.append(asyncio.create_task(scrape_crossweb_event(event_url)))

    await asyncio.gather(*tasks)


@backoff.on_exception(backoff.expo, Exception, max_tries=3)
async def scrape_crossweb_event(relative_url: str):
    base_url = "https://crossweb.pl"
    url = base_url + relative_url
    print(f"Scraping event: {url}")

    async with ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            response_text = await response.read()

    try:
        response_text = response_text.decode("utf-8")
    except UnicodeDecodeError:
        response_text = response_text.decode("ISO-8859-1")

    event_soup = BeautifulSoup(response_text, "html.parser")

    event_title = event_soup.find("h1", class_="h1-detail").text
    event_type = event_soup.find("div", class_="type").text
    event_category = event_soup.find("div", class_="category").text
    event_subject = event_soup.find("div", class_="subject").text
    event_date = event_soup.find("div", class_="date").text
    event_time = event_soup.find("div", class_="time").text
    event_language = event_soup.find("div", class_="language").text
    event_fee = event_soup.find("div", class_="fee").text
    event_city = event_soup.find("div", class_="city").text
    event_location = event_soup.find("div", class_="place").text
    event_location_address = event_soup.find("div", class_="address").text
    event_registration_link = event_soup.find("a", class_="btn btn-primary")["href"]
    event_webpage = event_soup.find("a", class_="btn btn-secondary")["href"]
    event_speakers: List[str] = event_soup.findall("div", class_="speakers").text
    event_agenda = event_soup.find("div", class_="agenda").text
    event_description = event_soup.find("div", class_="description").text


async def main():
    tasks = []
    for url in URLS:
        if "nikonferencje" in url:
            tasks.append(asyncio.create_task(scrape_unikon_events(url)))
        elif "eventbrite" in url:
            tasks.append(asyncio.create_task(scrape_brite_events(url)))
        elif "crossweb" in url:
            tasks.append(asyncio.create_task(scrape_crossweb_events(url)))

    print("Scraping started")
    await asyncio.gather(*tasks)
    print("Scraping complete")


def clear_output_dir():
    output_dir: str = os.getenv("SCRAPING_OUTPUT_DIR")
    if os.path.exists(output_dir):
        print("Removing existing output directory")
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)


if __name__ == "__main__":
    """
    try:
        with open("last_update_timestamp.txt", "r") as f:
            last_update_timestamp: str = f.read().strip()
            last_update_timestamp = datetime.strptime(last_update_timestamp, "%d-%m-%Y %H:%M")
    except FileNotFoundError:
        last_update_timestamp = None  # If the file doesn't exist, set to None
    """

    last_update_timestamp = None  # For testing purposes

    if last_update_timestamp is None or datetime.now() - last_update_timestamp > timedelta(hours=12):
        clear_output_dir()
        URLS: List[str] = os.getenv("SCRAPING_URLS").split(",")
        asyncio.run(main())

        # Update the last update timestamp
        with open("last_update_timestamp.txt", "w") as f:
            f.write(datetime.now().strftime("%d-%m-%Y %H:%M"))
    else:
        print("Last update was less than 12 hours ago. Skipping scraping.")
