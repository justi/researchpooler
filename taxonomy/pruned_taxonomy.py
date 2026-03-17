"""
Pruned taxonomy tree builder for two-stage classification.

Filters the full taxonomy config to include only branches under
pre-assigned L0 domains, reducing prompt size by >50%.
"""

import os
import yaml

TAXONOMY_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(TAXONOMY_DIR, "config.yaml")


def load_taxonomy_config_raw():
    """Load raw taxonomy config as a dict."""
    if not os.path.exists(CONFIG_PATH):
        return None
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def flatten_taxonomy(config):
    """Flatten taxonomy config dict to list of path strings."""
    paths = []

    def walk(node, prefix=""):
        if isinstance(node, list):
            for item in node:
                paths.append((prefix + " > " + item).strip(" > "))
        elif isinstance(node, dict):
            for key, val in node.items():
                new_prefix = (prefix + " > " + key).strip(" > ")
                if val is None:
                    paths.append(new_prefix)
                else:
                    walk(val, new_prefix)

    walk(config)
    return paths


def build_pruned_taxonomy(pre_domains, config=None):
    """Build a pruned taxonomy containing only branches from pre-assigned domains.

    Args:
        pre_domains: list of L0 domain names (e.g., ["Machine Learning", "Deep Learning"])
                     If empty or None, returns the full taxonomy (fallback).
        config: raw taxonomy config dict. If None, loads from config.yaml.

    Returns:
        list of taxonomy path strings for only the relevant domains.
    """
    if config is None:
        config = load_taxonomy_config_raw()

    if config is None:
        return []

    # Fallback: no pre-domains -> full taxonomy
    if not pre_domains:
        return flatten_taxonomy(config)

    # Filter to only the L0 domains in pre_domains
    pruned_config = {}
    for domain in pre_domains:
        if domain in config:
            pruned_config[domain] = config[domain]

    # If no matching domains found, fallback to full taxonomy
    if not pruned_config:
        return flatten_taxonomy(config)

    return flatten_taxonomy(pruned_config)
