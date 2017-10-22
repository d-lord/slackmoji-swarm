import unittest
from time import time
import scrape, config
from bs4 import BeautifulSoup
import requests
from tempfile import TemporaryDirectory
import asyncio, aiohttp


class PerfTesting(unittest.TestCase):

    __pairs_tested = 500  # if the file doesn't contain this many, we'll just test the ones it has

    def setUp(self):
        with open(config.in_file, 'r', encoding="UTF-8") as html:
            soup = BeautifulSoup(html, "html.parser")
        self.emoji_pairs = list(scrape.parse_emoji_from_html(soup))
        self.assertGreater(len(self.emoji_pairs), 0)  # I wish we could do this without consuming the generator :(

    def testProfile(self):
        with TemporaryDirectory() as dest:
            with aiohttp.ClientSession() as session:
                loop = asyncio.get_event_loop()
                start = time()
                loop.run_until_complete(scrape.download_all_emoji(self.emoji_pairs[:self.__pairs_tested], dest, session))
                end = time()
        print(f"Completed in {end - start} seconds.")
