import os
import re
import asyncio
import logging
import aiohttp
import aiofiles

from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Union
from urllib.parse import urlparse

import utils

logger = logging.getLogger(__name__)


def sanitize_filename(name: str, url: str) -> str:
    name = name.lower().strip().replace(" ", "_")
    name = re.sub(r"[^\w\d_-]", "", name)
    ext = os.path.splitext(urlparse(url).path)[-1]
    return f"{name}{ext or '.jpg'}"


class AsyncWikiImageDownloader:
    """
    Async downloader for representative images from Wikipedia animal pages.
    """

    def __init__(self, image_dir: str = "tmp", concurrency: int = 50):
        self.image_dir = image_dir
        self.concurrency = concurrency
        self.semaphore = asyncio.Semaphore(self.concurrency)
        os.makedirs(self.image_dir, exist_ok=True)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:138.0) Gecko/20100101 Firefox/138.0'
        }

    async def fetch_html(self, session: aiohttp.ClientSession, url: str) -> Optional[str]:
        try:
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    return await resp.text()
                logger.warning(f"Failed to fetch {url} - status {resp.status}")
        except Exception as e:
            logger.error(f"Exception fetching {url}: {e}")
        return None

    async def download_image(self, session: aiohttp.ClientSession, url: str, path: str) -> bool:
        try:
            async with session.get(url, timeout=10) as resp:
                if resp.status != 200:
                    logger.warning(f"Failed to download image {url} - status {resp.status}")
                    return False

                async with aiofiles.open(path, "wb") as f:
                    async for chunk in resp.content.iter_chunked(8192):
                        await f.write(chunk)
                        await f.flush()
                return True
        except Exception as e:
            logger.error(f"Error downloading image from {url}: {e}")
        return False

    def extract_image_url(self, soup: BeautifulSoup) -> Optional[str]:
        infobox = soup.find("table", class_=lambda c: c and "infobox biota" in c)
        img_tag = infobox.find("img") if infobox else soup.find("img", class_="mw-file-element")
        if img_tag and img_tag.get("src"):
            src = img_tag["src"]
            if src.startswith("//"):
                return "https:" + src
            elif src.startswith("/"):
                return "https://en.wikipedia.org" + src
            return src
        return None

    async def process_entry(self, entry: Dict[str, Union[str, None]], session: aiohttp.ClientSession):
        url = entry.get("wiki_url")
        name = entry.get("name", "unknown")

        if not url:
            logger.warning(f"No wiki URL for {name}")
            return

        # Predict the filename prefix without needing the image URL (assumes consistent naming)
        safe_name = re.sub(r"[^\w\d_-]", "", name.lower().strip().replace(" ", "_"))
        existing_files = [f for f in os.listdir(self.image_dir) if f.startswith(safe_name)]
        if existing_files:
            entry["local_image"] = os.path.join(self.image_dir, existing_files[0])
            logger.info(f"Image for {name} already exists as {existing_files[0]}")
            return

        async with self.semaphore:
            html = await self.fetch_html(session, url)
            if not html:
                return

            soup = BeautifulSoup(html, "html.parser")
            img_url = self.extract_image_url(soup)

            if not img_url:
                logger.warning(f"No image found for {name}")
                return

            filename = sanitize_filename(name, img_url)
            local_path = os.path.join(self.image_dir, filename)

            # After extracting the real image URL, also check if the exact file exists (just in case)
            if os.path.exists(local_path):
                entry["local_image"] = local_path
                logger.info(f"Cached (post-scrape): {name}")
                return

            logger.info(f"Downloading {name} from {img_url}")
            if await self.download_image(session, img_url, local_path):
                entry["local_image"] = local_path
                logger.info(f"Saved {name} as {filename}")

    @utils.log_timing
    async def download_images(self, mapping: Dict[str, List[Dict[str, Union[str, None]]]]):
        """
        Public method to kick off async downloads.
        """
        entries = [entry for sublist in mapping.values() for entry in sublist if entry.get("wiki_url")]
        connector = aiohttp.TCPConnector(limit=self.concurrency)
        async with aiohttp.ClientSession(headers=self.headers,connector=connector) as session:
            tasks = [self.process_entry(entry, session) for entry in entries]
            await asyncio.gather(*tasks)
