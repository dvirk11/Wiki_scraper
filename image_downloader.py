import os
import re
import requests

from bs4 import BeautifulSoup
from bs4.element import Tag
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
from typing import Dict, List, Optional, Union
import logging

import utils

logger = logging.getLogger(__name__)

class WikiImageDownloader:
    """
    A class to download representative images from Wikipedia animal pages.
    """

    def __init__(self, image_dir: str = "tmp", max_workers: int = 10):
        """
        Initialize the downloader.

        Args:
            image_dir (str): Directory to save downloaded images.
            max_workers (int): Number of threads for concurrent downloads.
        """
        self.image_dir = image_dir
        self.max_workers = max_workers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:138.0) Gecko/20100101 Firefox/138.0'
        }
        os.makedirs(self.image_dir, exist_ok=True)

    def sanitize_filename(self, name: str, url: str) -> str:
        """
        Create a filesystem-safe filename using the name and image URL.
        """
        name = name.lower().strip().replace(" ", "_")
        name = re.sub(r"[^\w\d_-]", "", name)
        ext = os.path.splitext(urlparse(url).path)[-1]
        return f"{name}{ext or '.jpg'}"

    def find_first_content_image(self, soup: BeautifulSoup) -> Optional[Tag]:
        """
        Try to find a representative image in the article HTML soup.
        """
        thumb_tag = soup.find(attrs={"typeof": "mw:File/Thumb"})
        if thumb_tag:
            img = thumb_tag.find("img", src=True)
            if img:
                return img

        file_tag = soup.find(attrs={"typeof": "mw:File"})
        if file_tag:
            img = file_tag.find("img", src=True)
            if img:
                return img

        img = soup.find("img", class_="mw-file-element")
        if img and img.get("src"):
            return img

        return None

    def download_image_from_entry(self, entry: Dict[str, Union[str, None]]) -> None:
        """
        Download the image for a single Wikipedia animal entry.
        """
        url = entry.get("wiki_url")
        name = entry.get("name", "unknown")

        if not url:
            logger.error(f"No wiki URL for {name}")
            return

        # Predict the filename without needing the image URL (assumes consistent naming)
        safe_name = re.sub(r"[^\w\d_-]", "", name.lower().strip().replace(" ", "_"))
        existing_files = [f for f in os.listdir(self.image_dir) if f.startswith(safe_name)]
        if existing_files:
            entry["local_image"] = os.path.join(self.image_dir, existing_files[0])
            logger.info(f"Image for {name} already exists as {existing_files[0]}")
            return

        try:
            res = requests.get(url, timeout=10, headers=self.headers)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, "html.parser")
            infobox = soup.find("table", class_=lambda c: c and "infobox biota" in c)
            img_tag = infobox.find("img") if infobox else None

            if not img_tag or not img_tag.get("src"):
                img_tag = self.find_first_content_image(soup)

            if not img_tag or not img_tag.get("src"):
                logger.error(f"No image found for {name}")
                return

            img_url = img_tag["src"]
            if img_url.startswith("//"):
                img_url = "https:" + img_url
            elif img_url.startswith("/"):
                img_url = "https://en.wikipedia.org" + img_url

            filename = self.sanitize_filename(name, img_url)
            local_path = os.path.join(self.image_dir, filename)

            logger.info(f"Downloading image for {name} from {img_url}")
            with requests.get(img_url, stream=True, timeout=10, headers=self.headers) as r:
                r.raise_for_status()
                with open(local_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

            entry["local_image"] = local_path
            logger.info(f"Downloaded {name}, saved as {filename}")

        except Exception as e:
            logger.error(f"Error downloading image for {name}: {e}")

    @utils.log_timing
    def download_images(self, mapping: Dict[str, List[Dict[str, Union[str, None]]]]) -> None:
        """
        Download images for all entries in a mapping grouped by category.
        """
        entries = [entry for sublist in mapping.values() for entry in sublist]
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            executor.map(self.download_image_from_entry, entries)
