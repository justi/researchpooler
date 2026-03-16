"""
Functions for PDF parsing tools and utils
"""

from pdfminer.high_level import extract_text
import tempfile
import urllib.request

def convertPDF(pdf_path):
    """
    Takes path to a PDF and returns the text inside it as string

    pdf_path: string indicating path to a .pdf file. Can also be a URL starting
              with 'http'
    returns string of the pdf, as it comes out raw from PDFMiner
    """

    if pdf_path[:4] == 'http':
        print('first downloading %s ...' % (pdf_path,))
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            with urllib.request.urlopen(pdf_path, timeout=30) as resp:
                tmp.write(resp.read())
            pdf_path = tmp.name

    return extract_text(pdf_path)
