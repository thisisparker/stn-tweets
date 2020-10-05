#!/usr/bin/env python3
import unittest

from stntweets import get_site_name


class TestSTNTweets(unittest.TestCase):
    def test_get_site_name_no_handle(self):
        self.assertEqual(get_site_name("Deutsche Welle", None), "Deutsche Welle")

    def test_get_site_name_handle(self):
        self.assertEqual(get_site_name("Deutsche Welle", "@dwnews"), "Deutsche Welle (@dwnews)")


if __name__=="__main__":
    unittest.main()
