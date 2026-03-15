"""
Functions for PDF parsing tools and utils
"""

from pdfminer.high_level import extract_text
from io import BytesIO
import urllib.request

def convertPDF(pdf_path, codec='utf-8'):
    """
    Takes path to a PDF and returns the text inside it as string

    pdf_path: string indicating path to a .pdf file. Can also be a URL starting
              with 'http'
    codec: can be 'ascii', 'utf-8', ...
    returns string of the pdf, as it comes out raw from PDFMiner
    """

    if pdf_path[:4] == 'http':
        print('first downloading %s ...' % (pdf_path,))
        urllib.request.urlretrieve(pdf_path, 'temp.pdf')
        pdf_path = 'temp.pdf'

    return extract_text(pdf_path)
