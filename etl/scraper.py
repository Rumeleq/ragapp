import asyncio
import os
import shutil
import traceback
from datetime import datetime, timedelta
from typing import List

import backoff
import requests
from aiohttp import ClientSession
from bs4 import BeautifulSoup, Tag
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
    event_urls: List[str] = [anchor["href"] for anchor in event_list_soup.find_all("a", class_="clearfix")]
    print(f"Found {len(event_urls)} events on Crossweb")

    tasks = []
    for event_url in event_urls:
        tasks.append(asyncio.create_task(scrape_crossweb_event(event_url)))

    await asyncio.gather(*tasks)


# @backoff.on_exception(backoff.expo, Exception, max_tries=3)
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
        print(f"Decoding error, trying ISO-8859-2: {url}")
        response_text = response_text.decode("ISO-8859-2")

    event_soup: BeautifulSoup = BeautifulSoup(response_text, "html.parser")
    event_details: dict[str] = {}

    try:
        # Extracting event title
        event_title = event_soup.find("div", class_="event-var fw-bold", itemprop="name")
        event_details["event_title"] = event_title.text.strip() if event_title else "N/A"

        # Extracting event type
        event_type_label = event_soup.find("div", class_="event-label", string="Typ wydarzenia:")
        event_details["event_type"] = event_type_label.find_next_sibling("div").text.strip() if event_type_label else "N/A"

        # Extracting event category
        event_category_label = event_soup.find("div", class_="event-label", string="Kategoria:")
        event_details["event_category"] = (
            event_category_label.find_next_sibling("div").text.strip() if event_category_label else "N/A"
        )

        # Extracting event subject
        event_subject_label = event_soup.find("div", class_="event-label", string="Tematyka:")
        event_details["event_subject"] = (
            event_subject_label.find_next_sibling("div").text.strip() if event_subject_label else "N/A"
        )

        # Extracting event date
        event_date_label = event_soup.find("div", class_="event-label", string="Data:")
        event_details["event_date"] = event_date_label.find_next_sibling("div").text.strip() if event_date_label else "N/A"

        # Extracting event time
        event_time_label = event_soup.find("div", class_="event-label", string="Godzina:")
        event_details["event_time"] = event_time_label.find_next_sibling("div").text.strip() if event_time_label else "N/A"

        # Extracting event language
        event_language_label = event_soup.find("div", class_="event-label", string="Język:")
        event_details["event_language"] = (
            event_language_label.find_next_sibling("div").text.strip() if event_language_label else "N/A"
        )

        # Extracting event fee
        event_fee_label = event_soup.find("div", class_="event-label", string="Wstęp:")
        event_details["event_fee"] = event_fee_label.find_next_sibling("div").text.strip() if event_fee_label else "N/A"

        # Extracting event city
        event_city_label = event_soup.find("div", class_="event-label", string="Miasto:")
        event_details["event_city"] = event_city_label.find_next_sibling("div").text.strip() if event_city_label else "N/A"

        # Extracting event location
        event_location_label = event_soup.find("div", class_="event-label", string="Miejsce:")
        event_details["event_location"] = (
            event_location_label.find_next_sibling("div").text.strip() if event_location_label else "N/A"
        )

        # Extracting event location address
        event_location_address_label = event_soup.find("div", class_="event-label", string="Adres:")
        event_details["event_location_address"] = (
            event_location_address_label.find_next_sibling("div").text.strip() if event_location_address_label else "N/A"
        )

        # Extracting event registration link
        event_registration_link = event_soup.find("a", class_="eventDetailLink.apply-link-js")
        event_details["event_registration_link"] = (
            event_registration_link["href"].strip() if event_registration_link else "N/A"
        )

        # Extracting event webpage
        event_webpage = event_soup.find("a", class_="eventDetailLink.apply-link-js", target="_blank")
        event_details["event_webpage"] = event_webpage["href"].strip() if event_webpage else "N/A"

        # Extracting event speakers
        event_speakers: List[Tag] = event_soup.find_all("div", class_="speaker-box")
        event_details["event_speakers"] = (
            [speaker.div.a["href"].strip() for speaker in event_speakers] if event_speakers else "N/A"
        )

        # Extracting event agenda
        # If there are two divs with this class, the first one contains the agenda;
        event_details_outer_div: List[Tag] = event_soup.find_all("div", class_="event-detail description")
        if len(event_details_outer_div) == 2:
            event_agenda = event_details_outer_div[0]
        else:
            event_agenda = None

        event_details["event_agenda"] = event_agenda.text.strip() if event_agenda else "N/A"

        # Extracting event description
        # Description shares the class with agenda, if present
        if len(event_details_outer_div) == 2:
            event_description = event_details_outer_div[1]
        elif len(event_details_outer_div) == 1:
            event_description = event_details_outer_div[0].find("div", class_="event-var ql-editor")
        else:
            event_description = None

        event_details["event_description"] = event_description.text.strip() if event_description else "N/A"

        # Setting source
        event_details["source"] = url
    except Exception as e:
        print(f"Error while scraping {url}: {e}")
        raise

    print(event_details)


async def main():
    tasks = []
    for url in URLS:
        if "unikonferencje" in url:
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
