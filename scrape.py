#!/usr/bin/env python3

"""
Scrapes emoji from one Slack team for export to another.
The export format is a directory containing 'emoji_name.[png|gif]' files for use with https://github.com/smashwilson/slack-emojinator.
The input is a saved .html file from https://<subdomain>.slack.com/customize/emoji. This saves the script from authenticating.
Async implementation based on https://iliauk.com/2016/03/07/high-performance-python-sessions-async-multi-tasking/.
"""

import config
import os
import asyncio, aiohttp
import logging
from bs4 import BeautifulSoup
from typing import Iterable, Tuple, Callable

logging.basicConfig(level=logging.INFO, format="%(asctime)-15s\t%(message)s")
logger = logging.getLogger(__name__)


def parse_emoji_from_html(soup: BeautifulSoup):
    """
    Generate (name, url) pairs of emoji by parsing a soup. Format defined 13-Oct-2017.
    :param soup:
    :return: (name, url) pairs of emoji.
    """
    all_emoji_rows = soup.find_all("tr", "emoji_row")
    for emoji_row in all_emoji_rows:
        url = emoji_row.find("td", headers="custom_emoji_image").span["data-original"]
        name = emoji_row.find("td", headers="custom_emoji_name").string.strip().replace(':', '')
        type = emoji_row.find("td", headers="custom_emoji_type").text
        if not type.startswith("Alias for"):
            yield (name, url)


def download_all_emoji(emoji_pairs: Iterable[Tuple[str, str]], output_dir: str, session: aiohttp.ClientSession):
    """
    Given (name, url) pairs, download them as output_dir/{name}.
    :param emoji_pairs: Iterable of (name, url) pairs. 'name'.png will become the filename.
    :param output_dir: Directory to save files to. Not checked for security.
    :param session: An aiohttp.ClientSession for the HTTP requests.
    :return: {"emoji name": Exception} for any failed requests.

    Credit to https://iliauk.com/2016/03/07/high-performance-python-sessions-async-multi-tasking/ for the async impl.
    """
    if not os.path.isdir(output_dir):
        logger.info(f"Creating output directory '{output_dir}'.")
        os.mkdir(config.output_dir)
    http_client = chunked_http_client(200, session)
    # http_client returns futures, save all the futures to a list
    tasks = [http_client(url, name) for name, url in emoji_pairs]
    errors = {}
    for future in asyncio.as_completed(tasks):
        data, name, url, *rest = yield from future
        if rest:
            logging.debug(f"Found extra info in the future: {rest}")
        try:
            handle_response(data, name, output_dir, url)
        except Exception as e:  # this catches errors during handling but not eg TimeoutErrors
            logger.error(f"Error for {name} - {e}")
            errors[name] = e
    return errors


def handle_response(data, name, output_dir, url):
    """
    Coroutine to handle an emoji download.
    :param data: The raw data from the response (probably a PNG file).
    :param name: The name of the emoji.
    :param output_dir: Directory to save the emoji to.
    :param url: URL the emoji was downloaded from.
    :return: None.
    """
    logger.info(f"Got {name.ljust(15)} {url}")
    ext = get_file_extension(url, name)
    with open(os.path.join(output_dir, name+ext), 'wb') as out:
        out.write(data)


def chunked_http_client(num_chunks, session, timeout=30):
    """
    Create an HTTP client respecting a maximum number of requests.
    :param num_chunks:
    :param session:
    :param timeout: Timeout for (in theory) an individual connection.
            However, this exception isn't handled correctly and the parameter seems to be taken as
            "all requests in the session must be done by {timeout} seconds else raise TimeoutError".
            Further experimentation is advised. Consider raising or setting to None for now.
    :return:
    """
    semaphore = asyncio.Semaphore(num_chunks)

    @asyncio.coroutine
    def http_get(url, name):
        nonlocal semaphore
        with (yield from semaphore):
            response = yield from session.get(url, timeout=timeout)
            body = yield from response.content.read()
            yield from response.wait_for_close()  # jeez, asyncio really likes yielding in coroutines
        return body, name, url
    return http_get


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
    with aiohttp.ClientSession() as session:
        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(download_all_emoji(all_emoji, config.output_dir, session))
        if results:
            print(f"Encountered errors in processing: {results}")