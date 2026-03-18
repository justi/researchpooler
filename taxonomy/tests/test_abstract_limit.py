"""Tests for abstract truncation removal (RE-29 F-4)."""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from taxonomy.classify import classify_batch


class TestAbstractLimit:
    """Tests verifying that abstract text is not truncated."""

    # TC-F4-001: Abstract >2000 chars included in full
    def test_long_abstract_not_truncated(self):
        """Verify that abstract >2000 chars is fully included in the prompt."""
        long_abstract = "x" * 3000
        papers = [{"title": "Test Paper", "abstract": long_abstract}]

        # We mock subprocess.run to capture the prompt
        with patch("taxonomy.classify.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = '{"type": "text", "part": {"text": "{\\"papers\\": []}"}}'
            mock_run.return_value = mock_result

            classify_batch(papers, ["Test > Topic"])

            # Check the prompt passed to opencode
            call_args = mock_run.call_args
            prompt = call_args[0][0][-1]  # Last arg is the prompt
            assert long_abstract in prompt, (
                "Full abstract (%d chars) should be in prompt" % len(long_abstract)
            )

    # TC-F4-002: Abstract exactly 2000 chars included without modification
    def test_exact_2000_chars_not_modified(self):
        """Verify that abstract of exactly 2000 chars is not modified."""
        abstract_2000 = "y" * 2000
        papers = [{"title": "Test Paper", "abstract": abstract_2000}]

        with patch("taxonomy.classify.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = '{"type": "text", "part": {"text": "{\\"papers\\": []}"}}'
            mock_run.return_value = mock_result

            classify_batch(papers, ["Test > Topic"])

            call_args = mock_run.call_args
            prompt = call_args[0][0][-1]
            assert abstract_2000 in prompt
