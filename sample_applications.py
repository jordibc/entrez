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
    """Sample Application 1: Converting GI numbers to accession numbers

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
    """Sample Application 2: Converting accession numbers to data

    Starting with a list of protein accession numbers, return the sequences in
    FASTA format.
    """
    # Input: comma-delimited list of accessions.
    accs = 'NM_009417,NM_000547,NM_001003009,NM_019353'.split(',')
    query = ' OR '.join(a + '[accn]' for a in accs)

    # Output: FASTA data.
    for line in entrez.on_search(db='nuccore', term=query,
                                 tool='fetch', rettype='fasta'):
        print(line)


def application_3():
    """Sample Application 3: Retrieving large datasets

    Download all chimpanzee mRNA sequences in FASTA format (>50,000 sequences).
    """
    query = 'chimpanzee[orgn] AND biomol mrna[prop]'
    with open('chimp.fna', 'w') as fout:
        for line in entrez.on_search(db='nucleotide', term=query,
                                     tool='fetch', rettype='fasta'):
            fout.write(line + '\n')
    print('The results are in file chimp.fna.')


def application_4():
    """Sample Application 4: Finding unique sets of linked records for each member of a large dataset

    Download separately the SNP rs numbers (identifiers) for each current gene
    on human chromosome 20.
    """
    query = 'human[orgn] AND 20[chr] AND alive[prop]'
    ids = []
    for line in entrez.equery(db='gene', term=query,
                              usehistory='y', retmax=5000):
        if line.strip().startswith('<Id>'):  # like:  <Id>6714</Id>
            ids.append(line.split('>')[1].split('<')[0])

    raw_params = ''.join('&id=%s' % x for x in ids)
    with open('snp_table', 'w') as fout:
        in_idlist = False
        links = []
        for line in entrez.equery(tool='link', raw_params=raw_params,
                                  dbfrom='gene', db='snp', linkname='gene_snp'):
            if '<IdList>' in line:
                in_idlist = True
            if '</IdList>' in line:
                in_idlist = False
            if '</LinkSet>' in line:
                fout.write(','.join(links) + '\n')
                links = []
            if '<Id>' in line:
                gid = line.split('<Id>')[1].split('</Id>')[0]
                if in_idlist:
                    fout.write('%s:' % gid)
                else:
                    links.append(gid)
    print('The results are in file snp_table.')

# Note that (as of Dec 2017) there is a mistake in the original perl code at
# https://www.ncbi.nlm.nih.gov/books/NBK25498/#chapter3.Application_4_Finding_unique_se
# It basically forgets to do "links = []" and so the snps accumulate for each
# successive gene that appears in the output file.



if __name__ == '__main__':
    # Let the user choose which sample to run.
    print('Examples from https://www.ncbi.nlm.nih.gov/books/NBK25498/')
    functions = [sample_1, sample_2, sample_3, sample_4,
                 application_1, application_2, application_3, application_4]
    docs = [f.__doc__.split('\n')[0] for f in functions]  # 1st line of docs

    while True:
        for i in range(len(functions)):
            print('  %3d - %s' % (i + 1, docs[i]))
        try:
            choice = int(raw_input('Sample to run: ')) - 1
            assert 0 <= choice < len(functions)
        except (ValueError, AssertionError, KeyboardInterrupt, EOFError):
            print('\nBye!')
            break
        functions[choice]()
