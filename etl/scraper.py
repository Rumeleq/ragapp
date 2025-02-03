import asyncio
import json
import os
import random
import re
import time
from datetime import datetime, timedelta
from typing import List

import aiofiles
import aiohttp
import backoff
import ftfy
from bs4 import BeautifulSoup, Tag
from dotenv import load_dotenv
from vector_saver import add_data_to_vector_storage, create_new_vector_storage

load_dotenv()


@backoff.on_exception(
    backoff.expo,
    (
        asyncio.TimeoutError,
        aiohttp.ClientError,
        aiohttp.ClientConnectorError,
        aiohttp.ClientConnectorDNSError,
        ConnectionRefusedError,
        AssertionError,
    ),
    max_tries=5,
    jitter=backoff.full_jitter,
)
async def get_soup_from_url(url: str) -> BeautifulSoup:
    """
    Retrieves a BeautifulSoup object from a URL, handling potential character encoding issues.
    :param url: URL to get the BeautifulSoup object from
    :return: BeautifulSoup object of the response with fixed characters
    """
    await asyncio.sleep(random.uniform(1, 3))
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=HEADERS) as response:
            response.raise_for_status()
            response_content: bytes = await response.read()

    try:
        response_text = response_content.decode("utf-8")
    except UnicodeDecodeError:
        response_text = response_content.decode("utf-8", errors="replace")
        response_text = ftfy.fix_text(response_text)
    response_text = re.sub(r"\s+", " ", response_text)
    soup: BeautifulSoup = BeautifulSoup(response_text, "html.parser")
    return soup


async def save_event_details(event_details: dict[str]) -> None:
    """
    Saves event details to a JSON file and adds them to the vector storage.
    :param event_details: Dictionary with event details to save
    :return: None
    """
    print(f"Saving event: {event_details['event_title']}")
    if event_details["event_title"] == "N/A":
        print(event_details)
        return

    event_id = re.sub(r'[<>:"/\\|?*]', "_", event_details["event_title"].replace(" ", "_"))

    async with aiofiles.open(f"{OUTPUT_DIR}/{event_id}.json", "w", encoding="utf-8") as f:
        await f.write(json.dumps(event_details, indent=4, ensure_ascii=False))

    await add_data_to_vector_storage(vector_storage, event_details, f"{OUTPUT_DIR}/{event_id}.json")


async def scrape_unikon_events(url: str) -> None:
    """
    Scrapes events from a given subset of events on unikonferencje.pl as defined by the URLs in .env file.
    Delegates scraping and saving of individual events to scrape_unikon_event().
    :param url: URL to scrape event URLs from
    :return: None
    """
    event_urls: List[str] = []
    page_index = 1
    while True:
        event_list_soup: BeautifulSoup = await get_soup_from_url(f"{url},s{page_index}")
        event_urls.extend(anchor["href"] for anchor in event_list_soup.find_all("a", property="url"))
        page_index += 1

        nav_anchors: List[Tag] = event_list_soup.find_all("a", class_="n-p")
        if len(nav_anchors) == 1 and "Poprzednie" in nav_anchors[0].text:
            break

    print(f"Found {len(event_urls)} events on Unikonferencje - {url.split('/')[-1]}")

    base_url = "https://unikonferencje.pl"

    tasks = []
    for event_url in event_urls:
        tasks.append(asyncio.create_task(scrape_unikon_event(base_url + event_url)))

    await asyncio.gather(*tasks)


async def scrape_unikon_event(url: str) -> None:
    """
    Scrapes details of a single event from unikonferencje.pl. Later saves the details to a JSON file via
    save_event_details().
    :param url: URL of the event to scrape and save
    :return: None
    """
    # Stops scraping for reappearing events which is specific to unikonferencje.pl
    if url in visited_urls:
        return
    visited_urls.add(url)
    event_soup: BeautifulSoup = await get_soup_from_url(url)
    event_details: dict[str] = {}

    # region Extracting event details

    # Extracting event title
    event_title_tag: Tag = event_soup.find("h2", property="name")
    event_title = event_title_tag.text.strip() if event_title_tag else "N/A"
    event_details["event_title"] = event_title

    # Finding divs for both time and location
    event_content_details_divs: List[Tag] = event_soup.find_all("div", class_="content-details-box")

    # Extracting event time
    event_time = event_content_details_divs[0].text.strip() if event_content_details_divs else "N/A"
    event_details["event_time"] = event_time

    # Extracting event location
    event_location = event_content_details_divs[1].text.strip() if event_content_details_divs else "N/A"
    event_details["event_location"] = event_location

    # Extracting event description
    event_description_tag: Tag = event_soup.find("div", class_="content-details-description")
    event_description = event_description_tag.text.strip() if event_description_tag else "N/A"
    event_details["event_description"] = event_description

    # Finding div for right column info
    event_right_column_div: Tag = event_soup.find("div", class_="content-info-column conference")
    # Extracting all divs inside
    event_right_column_divs: List[Tag] = event_right_column_div.find_all("div") if event_right_column_div else []

    # Extracting event fee
    event_fee_tag: Tag = event_right_column_divs[0]
    event_fee = event_fee_tag.text.strip() if event_fee_tag else "N/A"
    event_details["event_fee"] = event_fee

    # Extracting event organizers
    event_organizers_tag: Tag = event_right_column_divs[1]
    event_organizers = event_organizers_tag.text.strip() if event_organizers_tag else "N/A"
    event_details["event_organizers"] = event_organizers

    # Extracting event scientific disciplines
    event_disciplines_tag: Tag = event_right_column_divs[2]
    event_disciplines = event_disciplines_tag.text.strip() if event_disciplines_tag else "N/A"
    event_details["event_disciplines"] = event_disciplines

    # Extracting event keywords
    event_keywords_tag: Tag = event_right_column_divs[3]
    event_keywords = event_keywords_tag.text.strip() if event_keywords_tag else "N/A"
    event_details["event_keywords"] = event_keywords

    # Setting event source
    event_details["source"] = url

    # endregion

    await save_event_details(event_details)


async def scrape_brite_events(url: str) -> None:
    """
    Scrapes events from a given subset of events on eventbrite.com as defined by the URLs in .env file.
    Delegates scraping and saving of individual events to scrape_brite_event().
    :param url: URL to scrape event URLs from
    :return: None
    """
    event_urls: List[str] = []
    page_index = 1
    while True:
        event_list_soup: BeautifulSoup = await get_soup_from_url(f"{url[:-1]}{page_index}")
        event_urls.extend(anchor["href"] for anchor in event_list_soup.find_all("a", class_="event-card-link"))
        event_urls = list(set(event_urls))  # Remove duplicates
        page_index += 1

        next_page_button: Tag = event_list_soup.find("button", aria_label="Next Page")
        if next_page_button is None:
            break

    print(f"Found {len(event_urls)} events on Eventbrite - {url.split('/')[-2]}")

    tasks = []
    for event_url in event_urls:
        tasks.append(asyncio.create_task(scrape_brite_event(event_url)))

    await asyncio.gather(*tasks)


async def scrape_brite_event(url: str) -> None:
    """
    Scrapes details of a single event from eventbrite.com. Later saves the details to a JSON file via
    save_event_details().
    :param url: URL of the event to scrape and save
    :return: None
    """
    event_soup: BeautifulSoup = await get_soup_from_url(url)
    event_details: dict[str] = {}
    # region Extracting event details

    # Extracting event title
    event_title_tag: Tag = event_soup.find("h1", class_="event-title")
    event_title = event_title_tag.text.strip() if event_title_tag else "N/A"
    event_details["event_title"] = event_title

    # Extracting event summary
    event_summary_tag: Tag = event_soup.find("p", class_="summary")
    event_summary = event_summary_tag.text.strip() if event_summary_tag else "N/A"
    event_details["event_summary"] = event_summary

    # Extracting event date
    event_date_tag: Tag = event_soup.find("div", attrs={"data-testid": "display-date-container"})
    event_date = event_date_tag.text.strip() if event_date_tag else "N/A"
    event_details["event_date"] = event_date

    # Extracting event location
    event_location_tag: Tag = event_soup.find("div", class_="location-info__address")
    event_location = event_location_tag.text.strip() if event_location_tag else "N/A"

    # Remove button text
    if event_location_tag:
        button = event_location_tag.find("button")
        if button:
            button_text = button.text.strip()
            event_location = event_location.replace(button_text, "").strip()
    event_details["event_location"] = event_location

    # Extracting event fee
    event_fee_tag: Tag = event_soup.find("div", class_="conversion-bar__panel-info")
    event_fee = event_fee_tag.text.strip() if event_fee_tag else "N/A"
    event_fee = re.sub(r"(?<=zł)\s*", " ", event_fee)
    event_fee = re.sub(r"zł\s*(\d+)", r"\1 zł", event_fee)
    event_details["event_fee"] = event_fee

    # Extracting event refund policy
    event_refund_section: Tag = event_soup.find("section", attrs={"aria-labelledby": "refund-policy-heading"})
    event_refund_div: Tag = event_refund_section.find("div", class_=None) if event_refund_section else None
    event_refund_policy = event_refund_div.text.strip() if event_refund_div else "N/A"
    event_details["event_refund_policy"] = event_refund_policy

    # Extracting event organizer
    event_organizer_tag: Tag = event_soup.find("a", class_="descriptive-organizer-info-mobile__name-link")
    event_organizer = event_organizer_tag.text.strip() if event_organizer_tag else "N/A"
    event_organizer_profile = event_organizer_tag["href"].strip() if event_organizer_tag else "N/A"
    event_details["event_organizer"] = event_organizer
    event_details["event_organizer_profile"] = event_organizer_profile

    # Extracting event description
    event_description_tag: Tag = event_soup.find("div", class_="event-description")
    event_description = event_description_tag.text.strip() if event_description_tag else "N/A"
    event_details["event_description"] = event_description

    # Setting event source
    event_details["source"] = url

    # endregion

    await save_event_details(event_details)


async def scrape_crossweb_events(url: str) -> None:
    """
    Scrapes event URLs from crossweb.pl as defined by the URLs in .env file.
    Delegates scraping and saving of individual events to scrape_crossweb_event().
    :param url: URL to scrape event URLs from
    :return: None
    """
    event_list_soup: BeautifulSoup = await get_soup_from_url(url)
    event_urls: List[str] = [anchor["href"] for anchor in event_list_soup.find_all("a", class_="clearfix")]
    print(f"Found {len(event_urls)} events on Crossweb")

    base_url = "https://crossweb.pl"

    tasks = []
    for event_url in event_urls:
        tasks.append(asyncio.create_task(scrape_crossweb_event(base_url + event_url)))

    await asyncio.gather(*tasks)


async def scrape_crossweb_event(url: str) -> None:
    """
    Scrapes details of a single event from crossweb.pl. Later saves the details to a JSON file via
    save_event_details().
    :param url: URL of the event to scrape and save
    :return: None
    """
    event_soup: BeautifulSoup = await get_soup_from_url(url)
    event_details: dict[str] = {}

    # region Extracting event details
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
    event_details["event_registration_link"] = event_registration_link["href"].strip() if event_registration_link else "N/A"

    # Extracting event webpage
    event_webpage = event_soup.find("a", class_="eventDetailLink.apply-link-js", target="_blank")
    event_details["event_webpage"] = event_webpage["href"].strip() if event_webpage else "N/A"

    # Extracting event speakers
    event_speakers: List[Tag] = event_soup.find_all("div", class_="speaker-box")
    event_details["event_speakers"] = (
        ", ".join(speaker.div.a["href"].split("/")[2].replace("-", " ").strip() for speaker in event_speakers)
        if event_speakers
        else "N/A"
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
    # endregion

    await save_event_details(event_details)


async def main():
    start_time = time.perf_counter()

    tasks = []
    for url in URLS:
        if "unikonferencje" in url:
            tasks.append(asyncio.create_task(scrape_unikon_events(url)))
        if "eventbrite" in url:
            tasks.append(asyncio.create_task(scrape_brite_events(url)))
        elif "crossweb" in url:
            tasks.append(asyncio.create_task(scrape_crossweb_events(url)))

    print("Scraping started")
    await asyncio.gather(*tasks)
    print("Scraping complete")

    end_time = time.perf_counter()
    print(f"Total runtime: {end_time - start_time:.2f} seconds")


def clear_output_dir():
    if os.path.exists(OUTPUT_DIR):
        print("Removing existing output directory")
        print(os.listdir(OUTPUT_DIR))
        for file in os.listdir(OUTPUT_DIR):
            if file:
                os.remove(os.path.join(OUTPUT_DIR, file))
                print(f"Deleted: {os.path.join(OUTPUT_DIR, file)}")
    # os.makedirs(OUTPUT_DIR)


if __name__ == "__main__":
    print("ETL process is running, please wait...")
    """
    try:
        with open("last_update_timestamp.txt", "r") as f:
            last_update_timestamp: str = f.read().strip()
            last_update_timestamp = datetime.strptime(last_update_timestamp, "%d-%m-%Y %H:%M")
    except FileNotFoundError:
        last_update_timestamp = None  # If the file doesn't exist, set to None
    """

    last_update_timestamp = None  # For testing purposes

    if last_update_timestamp is None or datetime.now() - last_update_timestamp > timedelta(hours=6):
        OUTPUT_DIR = os.getenv("SCRAPING_OUTPUT_DIR")
        clear_output_dir()
        vector_storage = create_new_vector_storage()
        URLS: List[str] = os.getenv("SCRAPING_URLS").split(",")
        visited_urls = set()
        HEADERS = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        asyncio.run(main())

        # Update the last update timestamp
        with open("last_update_timestamp.txt", "w") as f:
            f.write(datetime.now().strftime("%d-%m-%Y %H:%M"))
    else:
        print("Last update was less than 12 hours ago. Skipping scraping.")
