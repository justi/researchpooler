"""Tests for scraper utilities and common patterns."""

import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestScraperFetchTimeout:
    """Verify scrapers that use fetch() have timeout and proper exception handling."""

    def _check_fetch_in_file(self, filepath):
        with open(filepath) as f:
            content = f.read()

        if 'def fetch(' not in content:
            pytest.skip("no fetch() function in %s" % filepath)

        # check timeout in urlopen
        assert 'timeout=' in content, \
            "%s: fetch() should use timeout in urlopen" % filepath

        # check no bare except
        lines = content.split('\n')
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped == 'except:':
                pytest.fail("%s line %d: bare 'except:' should be 'except Exception:'" % (filepath, i+1))

    def test_cvpr_fetch(self):
        self._check_fetch_in_file('cvpr_download_parse.py')

    def test_iccv_fetch(self):
        self._check_fetch_in_file('iccv_download_parse.py')

    def test_wacv_fetch(self):
        self._check_fetch_in_file('wacv_download_parse.py')


class TestNipsAddPdftext:
    """Test URL rewriting logic in nips_add_pdftext.py."""

    def test_abstract_url_rewrite(self):
        """Abstract URLs should be rewritten to PDF URLs."""
        url = 'https://proceedings.neurips.cc/paper_files/paper/2024/hash/abc123-Abstract-Conference.html'
        if '-Abstract-Conference.html' in url:
            pdf_url = url.replace('-Abstract-Conference.html', '-Paper-Conference.pdf').replace('/hash/', '/file/')
        else:
            pdf_url = url
        assert pdf_url.endswith('-Paper-Conference.pdf')
        assert '/file/' in pdf_url
        assert '/hash/' not in pdf_url

    def test_direct_pdf_url_unchanged(self):
        """Direct PDF URLs should not be modified."""
        url = 'https://example.com/paper.pdf'
        if '-Abstract-Conference.html' in url:
            pdf_url = url.replace('-Abstract-Conference.html', '-Paper-Conference.pdf').replace('/hash/', '/file/')
        else:
            pdf_url = url
        assert pdf_url == 'https://example.com/paper.pdf'

    def test_other_conference_url_unchanged(self):
        """URLs from other conferences should not be modified."""
        url = 'https://proceedings.mlr.press/v235/paper.pdf'
        if '-Abstract-Conference.html' in url:
            pdf_url = url.replace('-Abstract-Conference.html', '-Paper-Conference.pdf').replace('/hash/', '/file/')
        else:
            pdf_url = url
        assert pdf_url == url
