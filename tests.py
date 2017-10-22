import unittest
from time import time
import scrape, config
from bs4 import BeautifulSoup
import requests
from tempfile import TemporaryDirectory
import os


class PerfTesting(unittest.TestCase):

    __pairs_tested = 500  # if the file doesn't contain this many, we'll just test the ones it has

    def setUp(self):
        with open(config.in_file, 'r', encoding="UTF-8") as html:
            soup = BeautifulSoup(html, "html.parser")
        self.emoji_pairs = list(scrape.parse_emoji_from_html(soup))
        self.assertGreater(len(self.emoji_pairs), 0)  # I wish we could do this without consuming the generator :(

    def testWithoutConnectionReuse(self):
        with TemporaryDirectory() as dest:
            start = time()
            scrape.download_all_emoji(self.emoji_pairs[:self.__pairs_tested], dest, requests.get)
            end = time()
            count = len(os.listdir(dest))
        print(f"Completed {count} files in {end - start} seconds.")

    def testWithConnectionReuse(self):
        session = requests.Session()
        with TemporaryDirectory() as dest:
            start = time()
            scrape.download_all_emoji(self.emoji_pairs[:self.__pairs_tested], dest, session.get)
            end = time()
            count = len(os.listdir(dest))
        print(f"Completed {count} files in {end - start} seconds.")
        session.close()
