"""Tests for keyword post-processing normalization (RE-29 F-3)."""

import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from taxonomy.keyword_normalize import (
    normalize_keywords,
    depluralize_keyword,
    depluralize_word,
    PLURAL_EXCEPTIONS,
)


class TestDepluralizeWord:
    def test_basic_plural(self):
        assert depluralize_word("networks") == "network"

    def test_already_singular(self):
        assert depluralize_word("network") == "network"

    def test_short_word_unchanged(self):
        assert depluralize_word("us") == "us"


class TestDepluralizeKeyword:
    # TC-F3-001: "neural networks" -> "neural network"
    def test_neural_networks_stays_plural_exception(self):
        # "neural networks" is in the exception list
        assert depluralize_keyword("neural networks") == "neural networks"

    def test_regular_depluralization(self):
        assert depluralize_keyword("regret bounds") == "regret bound"

    def test_exception_list_terms_stay_plural(self):
        for term in PLURAL_EXCEPTIONS:
            assert depluralize_keyword(term) == term, (
                "Exception term '%s' should not be depluralized" % term
            )

    # TC-F3-002: Irregular plurals
    def test_irregular_plural_methods(self):
        result = depluralize_keyword("optimization methods")
        assert result == "optimization method"

    def test_single_word_keyword(self):
        # Single-word keywords are not depluralized (they get dropped later)
        assert depluralize_keyword("algorithms") == "algorithms"


class TestNormalizeKeywords:
    # TC-F3-004: Lowercase all keywords
    def test_lowercases_keywords(self):
        result = normalize_keywords(["Deep Learning", "NEURAL NETWORK"])
        assert all(kw == kw.lower() for kw in result)

    # TC-F3-005: Drop single-word terms
    def test_drops_single_word_keywords(self):
        result = normalize_keywords(["transformers", "deep learning", "optimization"])
        assert "transformers" not in result
        assert "optimization" not in result
        assert "deep learning" in result

    # TC-F3-006: Dedup against existing keywords
    def test_deduplicates_against_existing(self):
        existing = {"deep learning", "object detection"}
        result = normalize_keywords(
            ["Deep Learning", "object detection", "new method"],
            existing_keywords=existing,
        )
        assert "deep learning" in result
        assert "object detection" in result

    # TC-F3-007: Preserve multi-word domain terms
    def test_preserves_multi_word_terms(self):
        result = normalize_keywords([
            "reinforcement learning",
            "natural language processing",
            "graph neural networks",
        ])
        assert "reinforcement learning" in result
        assert "natural language processing" in result
        assert "graph neural networks" in result

    def test_removes_substring_keywords(self):
        result = normalize_keywords([
            "feature learning",
            "multi-task feature learning",
        ])
        assert "multi-task feature learning" in result
        assert "feature learning" not in result

    def test_handles_empty_input(self):
        assert normalize_keywords([]) == []
        assert normalize_keywords(None) == []

    def test_deduplicates_within_batch(self):
        result = normalize_keywords([
            "deep learning",
            "Deep Learning",
            "deep learning",
        ])
        assert result.count("deep learning") == 1

    # TC-F3-003: Reduces plural duplicates
    def test_depluralization_reduces_duplicates(self):
        keywords = [
            "regret bounds",
            "regret bound",
            "loss functions",
            "loss function",
            "topic models",
            "topic model",
        ]
        result = normalize_keywords(keywords)
        # After depluralization and dedup, should have no duplicates
        assert len(result) == len(set(result)), (
            "Found duplicates in result: %s" % result
        )

    def test_strips_whitespace(self):
        result = normalize_keywords(["  deep learning  ", "object detection "])
        assert "deep learning" in result
        assert "object detection" in result
