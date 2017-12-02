#!/usr/bin/env python

"""
Run with our interface the sample applications of the E-utilities
that appear in https://www.ncbi.nlm.nih.gov/books/NBK25498
"""

import entrez


def sample_1():
    """ESearch - ESummary/EFetch

    Download PubMed records that are indexed in MeSH for both asthma
    and leukotrienes and were also published in 2009.
    """
    # Input query.
    query = 'asthma[mesh] AND leukotrienes[mesh] AND 2009[pdat]'

    # Select the elements: query pubmed and keep the reference.
    elems = entrez.eselect(tool='search', db='pubmed', term=query)

    # XML document summaries.
    for line in entrez.eapply(tool='summary', db='pubmed', elems=elems):
        print(line)

    # Formatted data records (abstracts in this case).
    for line in entrez.eapply(tool='fetch', db='pubmed', elems=elems,
                              rettype='abstract'):
        print(line)

# We could do the same with:
#
#    query = 'asthma[mesh] AND leukotrienes[mesh] AND 2009[pdat]'
#
#    for line in entrez.on_search(db='pubmed', term=query, tool='summary'):
#        print(line)
#
#    for line in entrez.on_search(db='pubmed', term=query, tool='fetch',
#                                 rettype='abstract'):
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

    elems = entrez.eselect(tool='post', db='protein', id=id_list)

    # XML document summaries.
    for line in entrez.eapply(tool='summary', db='protein', elems=elems):
        print(line)

    # Formatted data records (FASTA in this case).
    for line in entrez.eapply(tool='fetch', db='protein', elems=elems,
                              rettype='fasta'):
        print(line)

# We could do the same with:
#
#    id_list = '194680922,50978626,28558982,9507199,6678417'
#
#    for line in entrez.on_search(db='protein', term=id_list, tool='summary'):
#        print(line)
#
#    for line in entrez.on_search(db='protein', term=id_list, tool='fetch',
#                                 rettype='fasta'):
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
    elems = entrez.eselect(tool='link', dbfrom='protein', db='gene', id=id_list,
                           linkname='protein_gene', cmd='neighbor_history')

    # XML document summaries of selected genes.
    for line in entrez.eapply(tool='summary', db='gene', elems=elems):
        print(line)

    # Formatted data records of selected genes (FASTA in this case).
    for line in entrez.eapply(tool='fetch', db='gene', elems=elems,
                              rettype='fasta'):
        print(line)


def sample_4():
    """ESearch - ELink - ESummary/EFetch

    Download protein FASTA records linked to abstracts published
    in 2009 that are indexed in MeSH for both asthma and leukotrienes.
    """
    # Input: Entrez text query in database pubmed.
    query = 'asthma[mesh] AND leukotrienes[mesh] AND 2009[pdat]'

    elems_pubmed = entrez.eselect(tool='search', db='pubmed', term=query)

    elems_prot = entrez.eselect(tool='link', dbfrom='pubmed', db='protein',
                                elems=elems_pubmed, linkname='pubmed_protein',
                                cmd='neighbor_history')

    # Linked XML Document Summaries from database protein.
    for line in entrez.eapply(tool='summary', db='protein', elems=elems_prot):
        print(line)

    # Formatted data records of selected proteins (FASTA in this case).
    for line in entrez.eapply(tool='fetch', db='protein', elems=elems_prot,
                              rettype='fasta'):
        print(line)

# TODO: all the other samples.
# EPost - ELink - ESummary/EFetch
# EPost - ESearch
# ELink - ESearch


def application_1():
    """Converting GI numbers to accession numbers.

    Starting with a list of nucleotide GI numbers, prepare a set of
    corresponding accession numbers.
    """
    # Input: comma-delimited list of GI numbers.
    gi_list = '24475906,224465210,50978625,9507198'

    for line in entrez.equery(tool='fetch', db='nucleotide',
                              id=gi_list, rettype='acc'):
        print(line)

    # The order of the accessions in the output will be the same order as the
    # GI numbers in gi_list


def application_2():
    """Converting accession numbers to data.

    Starting with a list of protein accession numbers, return the sequences in
    FASTA format.
    """
    # Input: comma-delimited list of accessions.
    accs = 'NM_009417,NM_000547,NM_001003009,NM_019353'.split(',')
    query = ' OR '.join(a + '[accn]' for a in accs)

    # Output: FASTA data.
    for line in entrez.on_search(db='nucleotide', term=query, tool='fetch',
                                 db2='protein', rettype='fasta'):
        print(line)

    # It is not working, but apparently neither is the original one.


def application_3():
    """Retrieving large datasets.

    Download all chimpanzee mRNA sequences in FASTA format (>50,000 sequences).
    """
    query = 'chimpanzee[orgn] AND biomol mrna[prop]'
    with open('chimp.fna', 'w') as fout:
        for line in entrez.on_search(db='nucleotide', term=query,
                                     tool='fetch', rettype='fasta'):
            fout.write(line + '\n')


# TODO: all the other applications.



if __name__ == '__main__':
    # Let the user choose which sample to run.
    samples = [sample_1, sample_2, sample_3, sample_4,
               application_1, application_2, application_3]
    while True:
        for i, f in enumerate(samples):
            print('  %3d - %s' % (i + 1, f.__doc__.split('\n')[0]))
        choice = raw_input('Sample to run (1-%d): ' % len(samples))
        if not choice.isdigit() or not 1 <= int(choice) <= len(samples):
            print('Bye!')
            break
        samples[int(choice) - 1]()
