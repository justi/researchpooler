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


def _rewrite_neurips_url(url):
    """Same logic as nips_download_parse.py and nips_add_pdftext.py."""
    pdf_url = url
    for abstract_suffix, paper_suffix in [
        ('-Abstract-Conference.html', '-Paper-Conference.pdf'),
        ('-Abstract-Datasets_and_Benchmarks.html', '-Paper-Datasets_and_Benchmarks.pdf'),
        ('-Abstract.html', '-Paper.pdf'),
    ]:
        if abstract_suffix in pdf_url:
            pdf_url = pdf_url.replace(abstract_suffix, paper_suffix).replace('/hash/', '/file/')
            break
    return pdf_url


class TestNeurIPSUrlRewrite:
    """Test URL rewriting for all NeurIPS URL formats (3 patterns)."""

    def test_new_format_conference(self):
        """2021+ Conference track: -Abstract-Conference.html"""
        url = 'https://proceedings.neurips.cc/paper_files/paper/2024/hash/abc-Abstract-Conference.html'
        pdf = _rewrite_neurips_url(url)
        assert pdf.endswith('-Paper-Conference.pdf')
        assert '/file/' in pdf
        assert '/hash/' not in pdf

    def test_new_format_datasets(self):
        """2021+ Datasets track: -Abstract-Datasets_and_Benchmarks.html"""
        url = 'https://proceedings.neurips.cc/paper_files/paper/2023/hash/abc-Abstract-Datasets_and_Benchmarks.html'
        pdf = _rewrite_neurips_url(url)
        assert pdf.endswith('-Paper-Datasets_and_Benchmarks.pdf')
        assert '/file/' in pdf

    def test_old_format(self):
        """2006-2020: -Abstract.html"""
        url = 'https://proceedings.neurips.cc/paper_files/paper/2006/hash/abc-Abstract.html'
        pdf = _rewrite_neurips_url(url)
        assert pdf.endswith('-Paper.pdf')
        assert '/file/' in pdf

    def test_direct_pdf_unchanged(self):
        url = 'https://example.com/paper.pdf'
        assert _rewrite_neurips_url(url) == url

    def test_other_conference_unchanged(self):
        url = 'https://proceedings.mlr.press/v235/paper.pdf'
        assert _rewrite_neurips_url(url) == url

    def test_no_double_rewrite(self):
        """Already-rewritten URL should not be modified."""
        url = 'https://proceedings.neurips.cc/paper_files/paper/2024/file/abc-Paper-Conference.pdf'
        assert _rewrite_neurips_url(url) == url
