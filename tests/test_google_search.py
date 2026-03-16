"""Tests for google_search.py (rewritten from dead Google AJAX API)"""

import os
import sys
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from google_search import getPDFURL


class TestGetPDFURL:
    def test_returns_notfound_on_no_results(self):
        fake_html = '<html><body>No results</body></html>'
        mock_resp = MagicMock()
        mock_resp.read.return_value = fake_html.encode('utf-8')
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        with patch('google_search.urllib.request.urlopen', return_value=mock_resp):
            assert getPDFURL('nonexistent paper') == 'notfound'

    def test_extracts_pdf_link(self):
        fake_html = '<a href="https://example.com/paper.pdf">link</a>'
        mock_resp = MagicMock()
        mock_resp.read.return_value = fake_html.encode('utf-8')
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        with patch('google_search.urllib.request.urlopen', return_value=mock_resp):
            assert getPDFURL('some paper') == 'https://example.com/paper.pdf'

    def test_returns_notfound_on_error(self):
        with patch('google_search.urllib.request.urlopen', side_effect=Exception('fail')):
            assert getPDFURL('some paper') == 'notfound'
