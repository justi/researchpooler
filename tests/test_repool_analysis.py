"""Tests for repool_analysis.py"""

import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repool_analysis import publicationSimilarityNaive


class TestPublicationSimilarityNaive:
    def test_identical_papers(self):
        pub = {'pdf_text': {'deep': 5, 'learning': 3, 'neural': 2}}
        scores = publicationSimilarityNaive([pub], pub)
        assert len(scores) == 1
        assert scores[0] == pytest.approx(1.0)

    def test_no_overlap(self):
        test = {'pdf_text': {'quantum': 1, 'physics': 1}}
        train = [{'pdf_text': {'cooking': 1, 'recipe': 1}}]
        scores = publicationSimilarityNaive(train, test)
        assert scores[0] == pytest.approx(0.0)

    def test_partial_overlap(self):
        test = {'pdf_text': {'deep': 5, 'learning': 3, 'neural': 2}}
        train = [{'pdf_text': {'deep': 2, 'learning': 1, 'vision': 4}}]
        scores = publicationSimilarityNaive(train, test)
        # overlap=2 (deep, learning), total words = 3+3=6
        assert scores[0] == pytest.approx(2.0 * 2 / 6)

    def test_missing_pdf_text_in_test(self):
        test = {'title': 'No text'}
        train = [{'pdf_text': {'word': 1}}]
        scores = publicationSimilarityNaive(train, test)
        assert scores == []

    def test_missing_pdf_text_in_train(self):
        test = {'pdf_text': {'word': 1}}
        train = [{'title': 'No text'}, {'pdf_text': {'word': 1}}]
        scores = publicationSimilarityNaive(train, test)
        assert scores[0] == -1
        assert scores[1] > 0

    def test_uses_set_intersection(self):
        """Verify the set-based overlap works correctly with many words."""
        words_a = {('word%d' % i): 1 for i in range(100)}
        words_b = {('word%d' % i): 1 for i in range(50, 150)}
        test = {'pdf_text': words_a}
        train = [{'pdf_text': words_b}]
        scores = publicationSimilarityNaive(train, test)
        # overlap = 50 words (word50-word99), total = 100+100 = 200
        assert scores[0] == pytest.approx(2.0 * 50 / 200)

    def test_empty_train(self):
        test = {'pdf_text': {'word': 1}}
        scores = publicationSimilarityNaive([], test)
        assert scores == []
