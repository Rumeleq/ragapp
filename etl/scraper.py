import asyncio
import os
import shutil
from typing import List

import requests
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()


def main():
    pass


def clear_output_dir():
    output_dir: str = os.getenv("SCRAPING_OUTPUT_DIR")
    if os.path.exists(output_dir):
        print(f"Removing existing output directory")
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)


if __name__ == "__main__":
    clear_output_dir()
    URLS: List[str] = os.getenv("SCRAPING_URLS").split(",")
    main()
