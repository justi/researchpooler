"""Tests for validation test harness (RE-29 F-5)."""

import os
import sys
import json
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from taxonomy.validate import (
    select_validation_papers,
    compare_runs,
    compute_jaccard,
    VALIDATION_CONFS,
    PAPERS_PER_CONF,
)


class TestPaperSelection:
    # TC-F5-001: 10 papers per conference from 5 conferences
    def test_selects_from_five_conferences(self):
        assert len(VALIDATION_CONFS) == 5

    def test_requests_ten_per_conference(self):
        assert PAPERS_PER_CONF == 10

    # TC-F5-003: Skip papers without abstracts
    def test_select_only_papers_with_abstracts(self):
        papers = select_validation_papers(seed=42)
        for p in papers:
            assert p.get("abstract"), (
                "Paper '%s' should have an abstract" % p["title"]
            )

    def test_deterministic_selection_with_seed(self):
        papers1 = select_validation_papers(seed=42)
        papers2 = select_validation_papers(seed=42)
        titles1 = [p["title"] for p in papers1]
        titles2 = [p["title"] for p in papers2]
        assert titles1 == titles2, "Same seed should produce same selection"


class TestComputeJaccard:
    def test_identical_sets(self):
        assert compute_jaccard({"a", "b"}, {"a", "b"}) == 1.0

    def test_disjoint_sets(self):
        assert compute_jaccard({"a"}, {"b"}) == 0.0

    def test_partial_overlap(self):
        result = compute_jaccard({"a", "b", "c"}, {"b", "c", "d"})
        assert abs(result - 0.5) < 0.01  # 2/4

    def test_empty_sets(self):
        assert compute_jaccard(set(), set()) == 1.0

    def test_one_empty(self):
        assert compute_jaccard({"a"}, set()) == 0.0


class TestCompareRuns:
    # TC-F5-002: Auto-comparison computes metrics
    def test_compare_computes_off_list_pct(self):
        allowed = ["ML > Core > Classification", "DL > Arch > Transformers"]
        run_a = {
            "Paper1": {
                "topics": ["ML > Core > Classification", "Invented Topic"],
                "keywords": ["deep learning"],
                "conf": "nips",
            }
        }
        run_b = {
            "Paper1": {
                "topics": ["ML > Core > Classification"],
                "keywords": ["deep learning"],
                "conf": "nips",
            }
        }

        report = compare_runs(run_a, run_b, allowed)
        assert "off_list_pct_a" in report["metrics"]
        assert "off_list_pct_b" in report["metrics"]
        assert report["metrics"]["off_list_pct_a"] == 50.0  # 1 of 2 off-list
        assert report["metrics"]["off_list_pct_b"] == 0.0  # 0 of 1 off-list

    def test_compare_computes_plural_pct(self):
        allowed = ["Test > Topic"]
        run_a = {
            "P1": {
                "topics": ["Test > Topic"],
                "keywords": ["neural networks", "neural network"],
                "conf": "nips",
            }
        }
        run_b = {
            "P1": {
                "topics": ["Test > Topic"],
                "keywords": ["neural network"],
                "conf": "nips",
            }
        }

        report = compare_runs(run_a, run_b, allowed)
        assert "plural_pct_a" in report["metrics"]
        assert "plural_pct_b" in report["metrics"]

    def test_compare_computes_overlap(self):
        allowed = ["T1", "T2", "T3"]
        run_a = {"P1": {"topics": ["T1", "T2"], "keywords": ["k1"], "conf": "nips"}}
        run_b = {"P1": {"topics": ["T2", "T3"], "keywords": ["k1"], "conf": "nips"}}

        report = compare_runs(run_a, run_b, allowed)
        assert "topics_overlap_avg" in report["metrics"]
        # Jaccard: {T2} / {T1,T2,T3} = 1/3
        assert abs(report["metrics"]["topics_overlap_avg"] - 1 / 3) < 0.01

    # TC-F5-004: Structured report output
    def test_report_is_structured(self):
        allowed = ["T1"]
        run_a = {"P1": {"topics": ["T1"], "keywords": ["k1"], "conf": "nips"}}
        run_b = {"P1": {"topics": ["T1"], "keywords": ["k1"], "conf": "nips"}}

        report = compare_runs(run_a, run_b, allowed)
        assert "timestamp" in report
        assert "paper_count" in report
        assert "metrics" in report
        assert "per_paper" in report
        assert isinstance(report["per_paper"], list)
        assert len(report["per_paper"]) == 1
