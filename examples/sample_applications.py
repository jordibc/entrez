#!/usr/bin/env python3

"""
Run with our interface the sample applications of the E-utilities
that appear in https://www.ncbi.nlm.nih.gov/books/NBK25498
"""

import sys

sys.path.append('..')
import entrez as ez


def sample_1():
    """ESearch - ESummary/EFetch

    Download PubMed records that are indexed in MeSH for both asthma
    and leukotrienes and were also published in 2009.
    """
    # Input query.
    query = 'asthma[mesh] AND leukotrienes[mesh] AND 2009[pdat]'

    # Select the elements: query pubmed and keep the reference.
    elems = ez.eselect(tool='search', db='pubmed', term=query)

    # XML document summaries.
    for line in ez.eapply(tool='summary', db='pubmed', elems=elems):
        print(line)

    # Formatted data records (abstracts in this case).
    for line in ez.eapply(tool='fetch', db='pubmed', elems=elems,
                          rettype='abstract'):
        print(line)

# We could do the same with:
#
#    query = 'asthma[mesh] AND leukotrienes[mesh] AND 2009[pdat]'
#
#    for line in ez.on_search(db='pubmed', term=query, tool='summary'):
#        print(line)
#
#    for line in ez.on_search(db='pubmed', term=query, tool='fetch',
#                             rettype='abstract'):
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

    elems = ez.eselect(tool='post', db='protein', id=id_list)

    # XML document summaries.
    for line in ez.eapply(tool='summary', db='protein', elems=elems):
        print(line)

    # Formatted data records (FASTA in this case).
    for line in ez.eapply(tool='fetch', db='protein', elems=elems,
                          rettype='fasta'):
        print(line)

# We could do the same with:
#
#    id_list = '194680922,50978626,28558982,9507199,6678417'
#
#    for line in ez.on_search(db='protein', term=id_list, tool='summary'):
#        print(line)
#
#    for line in ez.on_search(db='protein', term=id_list, tool='fetch',
#                             rettype='fasta'):
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
    # Input UIDs (protein GIs).
    id_list = '194680922,50978626,28558982,9507199,6678417'

    # Select elements, linking dbs protein and gene with the name protein_gene.
    elems = ez.eselect(tool='link', dbfrom='protein', db='gene', id=id_list,
                       linkname='protein_gene', cmd='neighbor_history')

    # XML document summaries of selected genes.
    for line in ez.eapply(tool='summary', db='gene', elems=elems):
        print(line)

    # Formatted data records of selected genes (FASTA in this case).
    for line in ez.eapply(tool='fetch', db='gene', elems=elems,
                          rettype='fasta'):
        print(line)


def sample_4():
    """ESearch - ELink - ESummary/EFetch

    Download protein FASTA records linked to abstracts published
    in 2009 that are indexed in MeSH for both asthma and leukotrienes.
    """
    # Input: Entrez text query in database pubmed.
    query = 'asthma[mesh] AND leukotrienes[mesh] AND 2009[pdat]'

    elems_pubmed = ez.eselect(tool='search', db='pubmed', term=query)

    elems_prot = ez.eselect(tool='link', dbfrom='pubmed', db='protein',
                            elems=elems_pubmed, linkname='pubmed_protein',
                            cmd='neighbor_history')

    # Linked XML Document Summaries from database protein.
    for line in ez.eapply(tool='summary', db='protein', elems=elems_prot):
        print(line)

    # Formatted data records of selected proteins (FASTA in this case).
    for line in ez.eapply(tool='fetch', db='protein', elems=elems_prot,
                          rettype='fasta'):
        print(line)


def sample_5():
    """EPost - ELink - ESummary/EFetch

    Downloads gene records linked to a set of proteins corresponding
    to a list of protein GI numbers.
    """
    # Input: List of Entrez UIDs in database protein (protein GIs).
    id_list = '194680922,50978626,28558982,9507199,6678417'

    elems_prot = ez.eselect(tool='post', db='protein', id=id_list)

    elems_gene = ez.eselect(tool='link', dbfrom='protein', db='gene',
                            elems=elems_prot, linkname='protein_gene',
                            cmd='neighbor_history')

    for line in ez.eapply(tool='summary', db='gene', elems=elems_gene):
        print(line)

    for line in ez.eapply(tool='fetch', db='gene', elems=elems_gene,
                          rettype='xml', retmode='xml'):
        print(line)


def sample_6():
    """EPost - ESearch

    Given an input set of protein GI numbers, create a history set containing
    the members of the input set that correspond to human proteins.
    (Which of these proteins are from human?)
    """
    id_list = '194680922,50978626,28558982,9507199,6678417'

    elems = ez.eselect(tool='post', db='protein', id=id_list)

    for line in ez.eapply(tool='search', db='protein', term='human[orgn]',
                          elems=elems):
        print(line)

# The way it is done in the original example, it would look like:
#    query = '#%s AND human[orgn]' % elems['QueryKey']
#    for line in ez.equery(tool='search', db='protein', term=query,
#                          WebEnv=elems['WebEnv'], usehistory='y'):
#        print(line)
# which is definitely uglier :)


def sample_7():
    """ELink - ESearch

    Given an input set of protein GI numbers, create a history set containing
    the gene IDs linked to members of the input set that also are on human
    chromosome X.
    (Which of the input proteins are encoded by a gene on human chromosome X?)
    """
    # Input: UIDs in database protein (protein GIs).
    id_list = '148596974,42544182,187937179,4557377,6678417'

    elems = ez.eselect(tool='link', dbfrom='protein', db='gene', id=id_list,
                       linkname='protein_gene', cmd='neighbor_history')

    query = 'human[orgn] AND x[chr]'
    for line in ez.eapply(tool='search', db='gene', term=query, elems=elems):
        print(line)


def application_1():
    """Sample Application 1: Converting GI numbers to accession numbers

    Starting with a list of nucleotide GI numbers, prepare a set of
    corresponding accession numbers.
    """
    # Input: comma-delimited list of GI numbers.
    gi_list = '24475906,224465210,50978625,9507198'

    for line in ez.equery(tool='fetch', db='nucleotide',
                          id=gi_list, rettype='acc'):
        print(line)

    # The order of the accessions in the output will be the same order as the
    # GI numbers in gi_list.


def application_2():
    """Sample Application 2: Converting accession numbers to data

    Starting with a list of protein accession numbers, return the sequences in
    FASTA format.
    """
    # Input: comma-delimited list of accessions.
    accs = 'NM_009417,NM_000547,NM_001003009,NM_019353'.split(',')
    query = ' OR '.join(a + '[accn]' for a in accs)

    # Output: FASTA data.
    for line in ez.on_search(db='nuccore', term=query,
                             tool='fetch', rettype='fasta'):
        print(line)


def application_3():
    """Sample Application 3: Retrieving large datasets

    Download all chimpanzee mRNA sequences in FASTA format (>50,000 sequences).
    """
    query = 'chimpanzee[orgn] AND biomol mrna[prop]'
    with open('chimp.fna', 'w') as fout:
        for line in ez.on_search(db='nucleotide', term=query,
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
    for line in ez.equery(tool='search', db='gene', term=query,
                          usehistory='y', retmax=5000):
        if line.strip().startswith('<Id>'):  # like:  <Id>6714</Id>
            ids.append(line.split('>')[1].split('<')[0])

    raw_params = ''.join('&id=%s' % x for x in ids)
    with open('snp_table', 'w') as fout:
        in_idlist = False
        links = []
        for line in ez.equery(tool='link', raw_params=raw_params,
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



try:
   input = raw_input  # in case this is run with python 2
except NameError:
   pass

if __name__ == '__main__':
    # Let the user choose which sample to run.
    print('Examples from https://www.ncbi.nlm.nih.gov/books/NBK25498/')
    functions = [
        sample_1, sample_2, sample_3, sample_4, sample_5, sample_6, sample_7,
        application_1, application_2, application_3, application_4]
    docs = [f.__doc__.split('\n')[0] for f in functions]  # 1st line of docs

    while True:
        for i in range(len(functions)):
            print('  %3d - %s' % (i + 1, docs[i]))
        try:
            choice = int(input('Sample to run: ')) - 1
            assert 0 <= choice < len(functions)
        except (ValueError, AssertionError, KeyboardInterrupt, EOFError):
            print('\nBye!')
            break
        functions[choice]()
