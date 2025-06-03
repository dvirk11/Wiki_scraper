# Wikipedia Scraper

## Overview
This project scrapes collateral adjectives and animal mappings from Wikipedia, downloads representative images asynchronously, and generates an HTML summary linking adjectives, animals, and their images.

## Features
- Scrapes Wikipedia pages to build a map of collateral adjectives linked to animals.
- Download images for each animal asynchronously to improve performance.
- Generates an `output.html` file summarizing the adjectives, animals, and downloaded images.
- Implements caching to avoid re-downloading existing images.
- Logs progress and errors to both console and a log file with timestamps.

## Installation
Clone the repository:

```bash
git clone https://github.com/dvirk11/Wiki_scraper.git
cd Wiki_scraper
```
## Install dependencies:
pip install -r requirements.txt

## Usage
Run the main script:

```bash
python main.py
```

This will:

Scrape the data.

Download images.

Generate an output.html file with the summary.

# Implementation Notes
## Table Selection Logic
The scraper selects tables[1] on the Wikipedia page because there was no reliable way to distinguish tables by class or id. This was necessary to correctly extract the relevant data.

## Performance Comparison: Async vs Threads
Both asynchronous and threaded solutions were tested.
Surprisingly, the threaded implementation was faster despite Python's GIL, likely because async overhead (context switching, event loop management) introduced additional latency.\
Both implements are attached. 

## Caching Mechanism
Images are cached locally to avoid re-downloading if the file already exists, speeding up subsequent runs.

## Logging
Logs are saved in wiki_scraper.log with timestamps.

## Running Tests
```bash
pytest test_wiki_scraper.py
```

Tests include:
Unit tests for sanitization and image finding \
Mocked download tests\
End-to-end (E2E) test simulating full Wikipedia page parsing and image saving


## Dependencies
Python 3.8+
aiohttp
aiofiles
beautifulsoup4

## Task Duration
The entire task took approximately 3.5 - 4 hours due to initial unfamiliarity with BeautifulSoup.
