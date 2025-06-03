import os
import shutil
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from image_downloader import WikiImageDownloader
from scraper import CollateralAdjectiveScraper, parse_cell_text
from bs4 import BeautifulSoup



@pytest.fixture
def temp_dir():
    dirpath = tempfile.mkdtemp()
    yield dirpath
    shutil.rmtree(dirpath)

def test_sanitize_filename_basic(temp_dir):
    downloader = WikiImageDownloader(image_dir=temp_dir)
    name = "Red Fox"
    url = "https://upload.wikimedia.org/image.jpg"
    result = downloader.sanitize_filename(name, url)
    assert result == "red_fox.jpg"

def test_find_first_content_image_returns_none_for_empty_soup():
    from bs4 import BeautifulSoup
    downloader = WikiImageDownloader()
    soup = BeautifulSoup("<html></html>", "html.parser")
    assert downloader.find_first_content_image(soup) is None

@patch("image_downloader.requests.get")
def test_download_image_from_entry_skips_if_exists(mock_get, temp_dir):
    # Create dummy file to simulate existing image
    dummy_name = "some_animal"
    dummy_file = os.path.join(temp_dir, f"{dummy_name}.jpg")
    with open(dummy_file, "w") as f:
        f.write("test")

    entry = {"name": "Some Animal", "wiki_url": "https://en.wikipedia.org/wiki/Some_Animal"}
    downloader = WikiImageDownloader(image_dir=temp_dir)

    downloader.download_image_from_entry(entry)

    # Since file already exists, requests.get should not be called
    mock_get.assert_not_called()
    assert "local_image" in entry
    assert entry["local_image"].endswith(".jpg")

@patch("image_downloader.requests.get")
def test_end_to_end_image_download(mock_get, temp_dir):
    html = """
    <html>
    <body>
        <table class="infobox biota">
            <tr>
                <td><img src="//upload.wikimedia.org/fake_image.jpg" /></td>
            </tr>
        </table>
    </body>
    </html>
    """
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.text = html

    img_response = MagicMock()
    img_response.iter_content = lambda chunk_size: [b"fakeimagedata"]
    img_response.__enter__.return_value = img_response
    img_response.raise_for_status = MagicMock()

    mock_get.side_effect = [mock_response, img_response]

    downloader = WikiImageDownloader(image_dir=temp_dir)
    mapping = {
        "mammals": [{"name": "Fake Animal", "wiki_url": "https://en.wikipedia.org/wiki/Fake_Animal"}]
    }
    downloader.download_images(mapping)

    # Validate image downloaded
    files = os.listdir(temp_dir)
    assert any(f.startswith("fake_animal") for f in files)
    assert "local_image" in mapping["mammals"][0]


def test_parse_cell_text_basic():
    html = '<td>Mammalian, <sup id="cite_ref">[1]</sup>Reptilian<br>Avian</td>'
    soup = BeautifulSoup(html, "html.parser")
    cell = soup.find("td")

    result = parse_cell_text(cell)
    assert result == ["Mammalian", "Reptilian", "Avian"]


@patch("scraper.requests.Session.get")
def test_get_collateral_adjectives_map_parsing(mock_get):
    html = """
    <html>
    <body>
        <table class="wikitable"></table>  <!-- Skipped -->
        <table class="wikitable">
            <tr><th>Animal</th><th>Collateral adjective</th></tr>
            <tr>
                <td><a href="/wiki/Cat">Cat</a></td>
                <td>Feline</td>
            </tr>
            <tr>
                <td><a href="/wiki/Dog">Dog</a></td>
                <td>Canine</td>
            </tr>
        </table>
    </body>
    </html>
    """
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = html
    mock_get.return_value = mock_resp

    scraper = CollateralAdjectiveScraper()
    result = scraper.get_collateral_adjectives_map()

    assert result["feline"][0]["name"] == "Cat"
    assert result["feline"][0]["wiki_url"] == "https://en.wikipedia.org/wiki/Cat"
    assert result["canine"][0]["name"] == "Dog"
