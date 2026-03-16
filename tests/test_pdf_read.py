"""Tests for pdf_read.py"""

import os
import sys
import tempfile
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pdf_read import convertPDF


class TestConvertPDF:
    def test_no_codec_parameter(self):
        """convertPDF should not accept a codec parameter (removed in review)."""
        import inspect
        sig = inspect.signature(convertPDF)
        assert 'codec' not in sig.parameters

    def test_uses_tempfile_for_urls(self):
        """URLs should be downloaded to a temp file, not fixed temp.pdf."""
        with patch('pdf_read.urllib.request.urlopen') as mock_urlopen, \
             patch('pdf_read.extract_text', return_value='text'):
            mock_resp = MagicMock()
            mock_resp.read.return_value = b'%PDF-fake'
            mock_resp.__enter__ = lambda s: s
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_resp

            result = convertPDF('http://example.com/paper.pdf')
            assert result == 'text'

            # verify urlopen was called with timeout
            call_args = mock_urlopen.call_args
            assert call_args[1].get('timeout', call_args[0][1] if len(call_args[0]) > 1 else None) == 30

    def test_local_file(self):
        """Local PDF paths should be passed directly to extract_text."""
        with patch('pdf_read.extract_text', return_value='extracted text') as mock_extract:
            result = convertPDF('/some/local/file.pdf')
            assert result == 'extracted text'
            mock_extract.assert_called_once_with('/some/local/file.pdf')

    def test_no_temp_pdf_file_created(self):
        """Should not create a fixed 'temp.pdf' file."""
        with patch('pdf_read.urllib.request.urlopen') as mock_urlopen, \
             patch('pdf_read.extract_text', return_value='text'):
            mock_resp = MagicMock()
            mock_resp.read.return_value = b'%PDF-fake'
            mock_resp.__enter__ = lambda s: s
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_resp

            convertPDF('http://example.com/paper.pdf')
            assert not os.path.exists('temp.pdf')
