"""
Integration tests that hit real conference proceedings sites.
These verify that scrapers still work against current HTML structures.

Run with: pytest tests/test_integration.py -v
Slower than unit tests (~30s) as they make real HTTP requests.
"""

import os
import sys
import urllib.request
import pytest
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

pytestmark = pytest.mark.skipif(
    os.environ.get('RUN_INTEGRATION_TESTS') != '1',
    reason='Set RUN_INTEGRATION_TESTS=1 to run'
)

HEADERS = {'User-Agent': 'Mozilla/5.0'}


def fetch(url, timeout=15):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as f:
        return f.read()


class TestNeurIPS:
    """Test NeurIPS scraper against proceedings.neurips.cc"""

    def test_paper_list_exists(self):
        html = fetch('https://proceedings.neurips.cc/paper_files/paper/2023')
        soup = BeautifulSoup(html, 'html.parser')
        paper_list = soup.find('ul', {'class': 'paper-list'})
        assert paper_list is not None, "paper-list element not found"

    def test_paper_has_title(self):
        html = fetch('https://proceedings.neurips.cc/paper_files/paper/2023')
        soup = BeautifulSoup(html, 'html.parser')
        paper_list = soup.find('ul', {'class': 'paper-list'})
        first_paper = paper_list.find('a', {'title': 'paper title'})
        assert first_paper is not None
        assert len(first_paper.text.strip()) > 5

    def test_pdf_url_is_valid(self):
        """PDF URL should point to actual PDF, not abstract page."""
        html = fetch('https://proceedings.neurips.cc/paper_files/paper/2023')
        soup = BeautifulSoup(html, 'html.parser')
        paper_list = soup.find('ul', {'class': 'paper-list'})
        first_link = paper_list.find('a', {'title': 'paper title'})
        page_url = 'https://proceedings.neurips.cc' + first_link['href']
        pdf_url = page_url.replace('-Abstract-Conference.html', '-Paper-Conference.pdf').replace('/hash/', '/file/')
        assert pdf_url.endswith('.pdf'), "PDF URL should end with .pdf"
        assert '/file/' in pdf_url


class TestICML:
    """Test ICML scraper against proceedings.mlr.press"""

    def test_papers_exist(self):
        html = fetch('https://proceedings.mlr.press/v235/')
        soup = BeautifulSoup(html, 'html.parser')
        papers = soup.find_all('div', {'class': 'paper'})
        assert len(papers) > 100, "Expected 100+ papers for ICML 2024"

    def test_paper_structure(self):
        html = fetch('https://proceedings.mlr.press/v235/')
        soup = BeautifulSoup(html, 'html.parser')
        paper = soup.find('div', {'class': 'paper'})
        title = paper.find('p', {'class': 'title'})
        authors = paper.find('span', {'class': 'authors'})
        assert title is not None and len(title.text.strip()) > 0
        assert authors is not None and len(authors.text.strip()) > 0


class TestCVPR:
    """Test CVPR scraper against openaccess.thecvf.com"""

    def test_papers_exist(self):
        html = fetch('https://openaccess.thecvf.com/CVPR2024?day=all')
        soup = BeautifulSoup(html, 'html.parser')
        papers = soup.find_all('dt', {'class': 'ptitle'})
        assert len(papers) > 100, "Expected 100+ papers for CVPR 2024"

    def test_paper_has_pdf_link(self):
        html = fetch('https://openaccess.thecvf.com/CVPR2024?day=all')
        soup = BeautifulSoup(html, 'html.parser')
        dt = soup.find('dt', {'class': 'ptitle'})
        # find next dd with pdf link
        for dd in dt.find_next_siblings('dd'):
            for a in dd.find_all('a'):
                if a.get('href', '').endswith('.pdf'):
                    assert True
                    return
        pytest.fail("No PDF link found for first paper")


class TestACLAnthology:
    """Test ACL Anthology scrapers"""

    def test_acl_papers_exist(self):
        html = fetch('https://aclanthology.org/events/acl-2024/')
        soup = BeautifulSoup(html, 'html.parser')
        papers = soup.find_all('strong')
        titled = [s for s in papers if s.find('a', class_='align-middle')]
        assert len(titled) > 100, "Expected 100+ papers for ACL 2024"

    def test_paper_has_pdf(self):
        html = fetch('https://aclanthology.org/events/acl-2024/')
        soup = BeautifulSoup(html, 'html.parser')
        pdf_link = soup.find('a', {'title': 'Open PDF'})
        assert pdf_link is not None
        assert pdf_link['href'].endswith('.pdf')


class TestAAI:
    """Test AAAI scraper against ojs.aaai.org"""

    def test_issue_has_papers(self):
        html = fetch('https://ojs.aaai.org/index.php/AAAI/issue/view/624')
        soup = BeautifulSoup(html, 'html.parser')
        articles = soup.find_all('div', class_='obj_article_summary')
        assert len(articles) > 50, "Expected 50+ papers in AAAI issue"

    def test_paper_structure(self):
        html = fetch('https://ojs.aaai.org/index.php/AAAI/issue/view/624')
        soup = BeautifulSoup(html, 'html.parser')
        article = soup.find('div', class_='obj_article_summary')
        title = article.find('h3', class_='title')
        authors = article.find('div', class_='authors')
        assert title is not None
        assert authors is not None


class TestOpenReview:
    """Test ICLR scraper against OpenReview API"""

    def test_api_returns_papers(self):
        import json
        url = 'https://api2.openreview.net/notes?content.venueid=ICLR.cc/2024/Conference&limit=5'
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=15) as f:
                data = json.loads(f.read())
            assert 'notes' in data
            assert len(data['notes']) > 0
        except urllib.error.HTTPError as e:
            if e.code == 403:
                pytest.skip("OpenReview API blocked this request (403)")
            raise


class TestPDFRead:
    """Test PDF download and extraction on a real PDF."""

    def test_convert_real_pdf(self):
        from pdf_read import convertPDF
        # Use a known working PDF URL from GitHub (PMLR hosts PDFs there)
        url = 'https://raw.githubusercontent.com/mlresearch/v235/main/assets/abad-rocamora24a/abad-rocamora24a.pdf'
        text = convertPDF(url)
        assert len(text) > 100, "Expected substantial text from PDF"
        assert not os.path.exists('temp.pdf'), "Should not create temp.pdf"
