#!/usr/bin/env python

"""
Run with our interface the sample applications of the E-utilities
that appear in http://www.ncbi.nlm.nih.gov/books/NBK25498
"""

from entrez import on_search, eselect, eapply


def sample_1():
    """ESearch - ESummary/EFetch

    Download PubMed records that are indexed in MeSH for both asthma
    and leukotrienes and were also published in 2009.
    """
    # Input query.
    query = 'asthma[mesh] AND leukotrienes[mesh] AND 2009[pdat]'

    # Select the elements: query pubmed and keep the reference.
    elems = eselect(tool='search', db='pubmed', term=query)

    # XML document summaries.
    for line in eapply(tool='summary', db='pubmed', elems=elems):
        print(line)

    # Formatted data records (abstracts in this case).
    for line in eapply(tool='fetch', db='pubmed', elems=elems,
                       rettype='abstract'):
        print(line)

# We could do the same with:
#
#    query = 'asthma[mesh] AND leukotrienes[mesh] AND 2009[pdat]'
#
#    for line in on_search(db='pubmed', term=query, tool='summary'):
#        print(line)
#
#    for line in on_search(db='pubmed', term=query, tool='fetch',
#                          rettype='abstract'):
#        print(line)
#
# by using on_search twice, we call 'search' two times instead
# of calling it once and keeping the resulting QueryKey and WebEnv
# for future queries. In many cases (as in these examples), you
# pay very little for that.


def sample_2():
    """EPost - ESummary/EFetch

    Download protein records corresponding to a list of GI numbers.
    """
    # Input: List of Entrez UIDs (integer identifiers, e.g. PMID, GI, Gene ID).
    id_list = '194680922,50978626,28558982,9507199,6678417'

    elems = eselect(tool='post', db='protein', id=id_list)

    # XML document summaries.
    for line in eapply(tool='summary', db='protein', elems=elems):
        print(line)

    # Formatted data records (FASTA in this case).
    for line in eapply(tool='fetch', db='protein', elems=elems,
                       rettype='fasta'):
        print(line)

# We could do the same with:
#
#    id_list = '194680922,50978626,28558982,9507199,6678417'
#
#    for line in on_search(db='protein', term=id_list, tool='summary'):
#        print(line)
#
#    for line in on_search(db='protein', term=id_list, tool='fetch',
#                          rettype='fasta'):
#        print(line)
#
# by using on_search we call first internally 'search' instead
# of 'post' as in the original example, but the resulting ids that
# will be used later are the same, so it works great.


def sample_3():
    """ELink - ESummary/Efetch

    Download gene records linked to a set of proteins corresponding to
    a list of GI numbers.
    """
    # Input UIDs (protein GIs)
    id_list = '194680922,50978626,28558982,9507199,6678417'

    # Select elements, linking dbs protein and gene with the name protein_gene
    elems = eselect(tool='link', dbfrom='protein', db='gene', id=id_list,
                    linkname='protein_gene', cmd='neighbor_history')

    # XML document summaries of selected genes.
    for line in eapply(tool='summary', db='gene', elems=elems):
        print(line)

    # Formatted data records of selected genes (FASTA in this case).
    for line in eapply(tool='fetch', db='gene', elems=elems,
                       rettype='fasta'):
        print(line)


# TODO: all the other sample applications.



if __name__ == '__main__':
    # Let the user choose which sample to run.
    samples = [sample_1, sample_2, sample_3]
    while True:
        try:
            choice = raw_input('Sample to run (1-%d): ' % len(samples))
            samples[int(choice) - 1]()
        except:
            break
