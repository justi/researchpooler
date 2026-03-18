"""Tests for pruned taxonomy tree builder (RE-29 F-2)."""

import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from taxonomy.pruned_taxonomy import (
    build_pruned_taxonomy,
    flatten_taxonomy,
    load_taxonomy_config_raw,
)

# Sample taxonomy config for testing
SAMPLE_CONFIG = {
    "Machine Learning": {
        "Core Methods": [
            "Classification",
            "Clustering",
            "Regression",
        ],
        "Learning Types": [
            "Active Learning",
            "Adversarial Learning",
        ],
    },
    "Deep Learning": {
        "Architectures": [
            "Transformers",
            "Neural Networks",
        ],
        "Models": [
            "Diffusion Models",
        ],
    },
    "Computer Vision": {
        "Analysis": [
            "Object Detection",
            "Semantic Segmentation",
        ],
    },
}


class TestFlattenTaxonomy:
    def test_flatten_produces_l0_l1_l2_paths(self):
        paths = flatten_taxonomy(SAMPLE_CONFIG)
        assert "Machine Learning > Core Methods > Classification" in paths
        assert "Deep Learning > Architectures > Transformers" in paths
        assert "Computer Vision > Analysis > Object Detection" in paths

    def test_flatten_count(self):
        paths = flatten_taxonomy(SAMPLE_CONFIG)
        assert len(paths) == 10  # 3 + 2 + 2 + 1 + 2 = 10


class TestBuildPrunedTaxonomy:
    # TC-F2-001: Only branches from pre-assigned domains
    def test_single_domain_includes_only_that_domain(self):
        paths = build_pruned_taxonomy(["Machine Learning"], SAMPLE_CONFIG)
        for p in paths:
            assert p.startswith("Machine Learning"), (
                "Path %s should start with Machine Learning" % p
            )
        assert len(paths) == 5  # 3 + 2

    def test_multi_domain_includes_only_those_domains(self):
        paths = build_pruned_taxonomy(
            ["Machine Learning", "Deep Learning"], SAMPLE_CONFIG
        )
        for p in paths:
            assert p.startswith("Machine Learning") or p.startswith(
                "Deep Learning"
            ), "Path %s should be from ML or DL" % p
        assert len(paths) == 8  # 5 + 3

    # TC-F2-002: Single-domain <= 4k chars
    def test_single_domain_size_under_4k_chars(self):
        config = load_taxonomy_config_raw()
        if config is None:
            pytest.skip("config.yaml not available")
        # Test each domain individually
        for domain in config:
            paths = build_pruned_taxonomy([domain], config)
            total_chars = sum(len(p) for p in paths)
            assert total_chars <= 4000, (
                "Domain %s produces %d chars (> 4000)" % (domain, total_chars)
            )

    # TC-F2-003: Multi-domain (3) <= 4k chars
    def test_three_domain_size_under_4k_chars(self):
        config = load_taxonomy_config_raw()
        if config is None:
            pytest.skip("config.yaml not available")
        domains = list(config.keys())[:3]
        paths = build_pruned_taxonomy(domains, config)
        total_chars = sum(len(p) for p in paths)
        assert total_chars <= 4000, (
            "3-domain pruned taxonomy produces %d chars (> 4000)" % total_chars
        )

    # TC-F2-004: No pre-domains -> full taxonomy
    def test_empty_pre_domains_returns_full_taxonomy(self):
        full = flatten_taxonomy(SAMPLE_CONFIG)
        assert build_pruned_taxonomy(None, SAMPLE_CONFIG) == full
        assert build_pruned_taxonomy([], SAMPLE_CONFIG) == full

    # TC-F2-005: Valid tree structure
    def test_pruned_paths_are_valid_subset_of_full(self):
        full = set(flatten_taxonomy(SAMPLE_CONFIG))
        pruned = build_pruned_taxonomy(["Deep Learning"], SAMPLE_CONFIG)
        for p in pruned:
            assert p in full, "Pruned path %s not in full taxonomy" % p

    def test_nonexistent_domain_returns_full_taxonomy(self):
        full = flatten_taxonomy(SAMPLE_CONFIG)
        paths = build_pruned_taxonomy(["Nonexistent Domain"], SAMPLE_CONFIG)
        assert paths == full, "Nonexistent domain should fallback to full taxonomy"

    def test_loads_config_from_file_when_none(self):
        # This tests the default config loading path
        paths = build_pruned_taxonomy(None)
        if paths:  # Only test if config.yaml exists
            assert len(paths) > 0
            assert all(">" in p for p in paths if " " in p)
