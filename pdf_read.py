"""
Functions for PDF parsing tools and utils
"""

from pdfminer.high_level import extract_text
import os
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
        req = urllib.request.Request(pdf_path, headers={'User-Agent': 'Mozilla/5.0'})
        tmp = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                tmp.write(resp.read())
            tmp.close()
            return extract_text(tmp.name)
        finally:
            tmp.close()
            os.unlink(tmp.name)

    return extract_text(pdf_path)
