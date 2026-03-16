"""Tests for repool_util.py"""

import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repool_util import savePubs, loadPubs, stringToWordDictionary


class TestSaveLoadPubs:
    def test_roundtrip(self, tmp_path):
        pubs = [
            {'title': 'Paper One', 'authors': ['Alice', 'Bob'], 'year': 2024, 'venue': 'NeurIPS 2024'},
            {'title': 'Paper Two', 'authors': ['Charlie'], 'year': 2023, 'venue': 'ICML 2023'},
        ]
        path = str(tmp_path / "pubs_test")
        savePubs(path, pubs)
        loaded = loadPubs(path)
        assert len(loaded) == 2
        assert loaded[0]['title'] == 'Paper One'
        assert loaded[1]['authors'] == ['Charlie']

    def test_empty_list(self, tmp_path):
        path = str(tmp_path / "pubs_empty")
        savePubs(path, [])
        loaded = loadPubs(path)
        assert loaded == []

    def test_binary_mode(self, tmp_path):
        """Verify pickle files are written in binary mode."""
        path = str(tmp_path / "pubs_bin")
        savePubs(path, [{'title': 'test'}])
        with open(path, 'rb') as f:
            header = f.read(2)
        # pickle protocol 2+ starts with \x80
        assert header[0] == 0x80


class TestStringToWordDictionary:
    def test_basic(self):
        d = stringToWordDictionary("hello world hello")
        assert d['hello'] == 2
        assert d['world'] == 1

    def test_stopwords_removed(self):
        d = stringToWordDictionary("the quick brown fox and the lazy dog")
        assert 'the' not in d
        assert 'and' not in d
        assert 'quick' in d
        assert 'brown' in d

    def test_short_words_filtered(self):
        d = stringToWordDictionary("I am a big fan of AI")
        # words with len <= 2 should be filtered
        assert 'am' not in d
        assert 'big' in d
        assert 'fan' in d

    def test_case_insensitive(self):
        d = stringToWordDictionary("Hello HELLO hello")
        assert d['hello'] == 3

    def test_cid_removed(self):
        """cid is a PDF artifact that should be removed."""
        d = stringToWordDictionary("some text with cid artifacts cid")
        assert 'cid' not in d

    def test_those_and_may_separate(self):
        """Regression: 'those' and 'may' were concatenated due to missing comma."""
        d = stringToWordDictionary("those may also appear here often")
        assert 'thosemay' not in d
        assert 'those' not in d  # stopword
        assert 'may' not in d    # stopword
        assert 'also' not in d   # stopword

    def test_empty_string(self):
        d = stringToWordDictionary("")
        assert d == {}

    def test_no_dict_mutation_error(self):
        """Regression: dict changed size during iteration in Python 3."""
        text = "the and for that can this which where are from"
        d = stringToWordDictionary(text)
        # all stopwords, should return empty dict
        assert d == {}
