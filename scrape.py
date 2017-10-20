#!/usr/bin/env python3

"""
Scrapes emoji from one Slack team for export to another.
The export format is specified by https://github.com/lambtron/emojipacks. (note the yaml write isn't actually implemented yet.)
The input is a saved .html file from https://<subdomain>.slack.com/customize/emoji. This saves the script from authenticating.
"""

import config
import os
import requests
import logging
from bs4 import BeautifulSoup
from typing import Iterable, Tuple, Callable

logging.basicConfig(level=logging.INFO, format="%(asctime)-15s\t%(message)s")
logger = logging.getLogger(__name__)


def parse_emoji_from_html(soup: BeautifulSoup):
    """
    Generate (name, url) pairs of emoji by parsing a soup. Format defined 13-Oct-2017.
    :param soup:
    :return:
    """
    all_emoji_rows = soup.find_all("tr", "emoji_row")
    for emoji_row in all_emoji_rows:
        url = emoji_row.find("td", headers="custom_emoji_image").span["data-original"]
        name = emoji_row.find("td", headers="custom_emoji_name").string.strip().replace(':', '')
        type = emoji_row.find("td", headers="custom_emoji_type").text
        if not type.startswith("Alias for"):
            yield (name, url)


def download_all_emoji(emoji_pairs: Iterable[Tuple[str, str]], output_dir: str,
                       fetch_method: Callable[..., requests.Response]=None):
    """
    Given (name, url) pairs, download them as output_dir/{name}.
    :param emoji_pairs: Iterable of (name, url) pairs. 'name'.png will become the filename.
    :param output_dir: Directory to save files to. Not checked for security.
    :param fetch_method: A 'requests' type method. Defaults to a new requests.Session().get.
    :return: Nothing interesting.
    """
    if not fetch_method:
        session = requests.Session()
        fetch_method = session.get
    if not os.path.isdir(output_dir):
        logger.info(f"Creating output directory '{output_dir}'.")
        os.mkdir(config.output_dir)
    for pair in emoji_pairs:
        name, url = pair
        logger.info(f"{name.ljust(15)} {url}")
        r = fetch_method(url)
        ext = get_file_extension(url, name)
        with open(os.path.join(output_dir, name+ext), 'wb') as out:
            out.write(r.content)


def get_file_extension(url, name=None, log=True):
    """
    Split a URL and return the file extension.
    :param url: Input data (eg 'https://foo.com/image.png')
    :param name: A 'friendly name' for logging warnings.
    :param log: Whether to log warnings on dodgy input.
    :return: '.png' for the sample input.
    """
    start = url.rfind('.')
    if start == -1 and log:
        logger.warning(f"Dodgy file extension on last character for {name}: using no extension")
    ext = url[start:]
    if len(url) - start < 4:
        logger.warning(f"Dodgy file extension for {name}: using anyway: '{ext}'")
    return ext

if __name__ == "__main__":
    """
    Use the config file to kick off a mass download.
    """
    with open(config.in_file, 'r', encoding="UTF-8") as html:
        soup = BeautifulSoup(html, "html.parser")
    all_emoji = parse_emoji_from_html(soup)
    download_all_emoji(all_emoji, config.output_dir)