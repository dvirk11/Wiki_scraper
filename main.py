import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional

from image_downloader import WikiImageDownloader
from scraper import CollateralAdjectiveScraper
from async_image_downloader import AsyncWikiImageDownloader
from html_generator import generate_html


log_filename = f"wiki_scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


async def main() -> None:
    """
    Main entry point for the pipeline:
    1. Scrapes collateral adjectives and animal mappings from Wikipedia.
    2. Download images for each animal.
    3. Generates an HTML summary file linking adjectives, animals, and images.
    """
    logger.info("Scraping data from Wikipedia")
    scraper = CollateralAdjectiveScraper()
    mapping: Dict[str, List[Dict[str, Optional[str]]]] = scraper.get_collateral_adjectives_map()

    # logger.info("Downloading images")
    # downloader = AsyncWikiImageDownloader()
    # await downloader.download_images(mapping)

    logger.info("Downloading images")
    downloader = WikiImageDownloader()
    downloader.download_images(mapping)

    logger.info("Generating HTML")
    html_path: str = generate_html(mapping)

    logger.info(f"Done. HTML saved to: {html_path}")


if __name__ == "__main__":
    asyncio.run(main())  # ✅ run the async main
