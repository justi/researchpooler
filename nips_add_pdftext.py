"""
Standalone helper script.

Load nips pubs_ file, and adds to every paper its word counts under key
'pdf_text'. The PDF for each paper is downloaded from NIPS site.
"""

from repool_util import loadPubs, savePubs, stringToWordDictionary
from pdf_read import convertPDF

pubs_all = loadPubs('pubs_nips')
print('loaded pubs with %d entries.' % (len(pubs_all),))

# possibly place restrictions on pubs to process here
pubs = pubs_all

for i, p in enumerate(pubs):

    # if the pdf url does not exist, in future this could possibly use google
    # search to try to look up a link for the pdf first.
    if 'pdf' in p and 'pdf_text' not in p:

        # convert abstract page URL to direct PDF URL (handles multiple formats)
        pdf_url = p['pdf']
        for abstract_suffix, paper_suffix in [
            ('-Abstract-Conference.html', '-Paper-Conference.pdf'),
            ('-Abstract-Datasets_and_Benchmarks.html', '-Paper-Datasets_and_Benchmarks.pdf'),
            ('-Abstract.html', '-Paper.pdf'),
        ]:
            if abstract_suffix in pdf_url:
                pdf_url = pdf_url.replace(abstract_suffix, paper_suffix).replace('/hash/', '/file/')
                break

        processed = False
        try:
            print('downloading pdf for [%s] and parsing...' % (p.get('title', 'an un-titled paper')))
            txt = convertPDF(pdf_url)
            processed = True
            print('processed!')
        except Exception as e:
            print('error: unable to download the pdf from %s: %s' % (pdf_url, e))
            print('skipping...')

        if processed:
            # convert to bag of words and store
            try:
                p['pdf_text'] = stringToWordDictionary(txt)
            except Exception as e:
                print('was unable to convert text to bag of words: %s. Skipped.' % (e,))

    print('%d/%d = %.2f%% done.' % (i+1, len(pubs), 100*(i+1.0)/len(pubs)))

savePubs('pubs_nips', pubs_all)
