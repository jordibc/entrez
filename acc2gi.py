#!/usr/bin/env python3

"""
Use Entrez utilities to get the GIs of the given accession
numbers, or the ones that can be extracted from some fasta files.
"""

import sys
import re
import argparse

import entrez


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-f', '--fastas', metavar='FILE', nargs='+',
                       help='fasta files with the accession numbers')
    group.add_argument('-a', '--accessions', metavar='ACC', nargs='+',
                       help='accession numbers')
    parser.add_argument('-n', '--nreq', type=int, default=100,
                        help='number of accession numbers per request')
    parser.add_argument('-m', '--max', type=int, default=-1,
                        help='maximum number to query')
    parser.add_argument('-c', '--check', action='store_true',
                        help='just check duplicate accession numbers')
    args = parser.parse_args()

    # If in "check mode", just check for duplicate accession numbers and exit.
    if args.check:
        if not args.fastas:
            sys.exit('Missing fasta files to check.')
        print_duplicates(args.fastas)
        sys.exit()

    # Get accessions from the given list if given, or from the given files.
    accessions = args.accessions or read_accessions(args.fastas)

    # Print the GIs and accession numbers for all accession numbers,
    # in groups of args.nreq numbers per request to the NCBI webservers.
    total_requests = args.max if args.max >= 0 else len(accessions)
    for i in range(0, total_requests, args.nreq):
        print_acc2gi(accessions[i:min(i + args.nreq, total_requests)])



def print_acc2gi(accessions):
    """Print GIs corresponding to the given accession numbers."""
    term = ' OR '.join(a + '[accn]' for a in accessions)
    for line in entrez.on_search(db='nucleotide', term=term, tool='summary'):
        if 'Name="Extra"' in line and any(a in line for a in accessions):
            gi = re.search('gi\|([0-9]+)\|', line).group(1)
            acc = re.search('((emb)|(gb)|(ref)|(dbj))\|(?P<acc>\w+\.[0-9]+)\|',
                            line).group('acc')
            print('%18s  ->  %s' % (acc, gi))


def read_accessions(fnames):
    """Return a list of accession numbers from a list of fasta files."""
    accessions = []
    for fname in fnames:
        for line in open(fname):
            if line.startswith('>'):  # header with the accession number info
                raw = line.strip('> \n').split(' ', 1)[0]  # take the beginning
                accessions.append(parse(raw))
    return accessions


def parse(raw):
    """Return the accession number contained in the raw string of a fasta."""
    # A quite sui-generis parser to get the accession numbers.

    # For example, with the given inputs on the left, it returns...
    #   X64695.1.gene9                 ->  X64695.1
    #   VanY-D_4_AY489045              ->  AY489045
    #   2:1314_M29695.1                ->  M29695.1
    #   (Tmt)DfrB4:FM87748469-305:237  ->  FM87748469

    if re.search('NC_\d+', raw):            # Eg: NC_013773
        return re.search('NC_\d+', raw).group()
    elif re.search('NZ_[A-Z0-9]+', raw):    # Eg: NZ_AGSO01000004.1
        return re.search('NZ_[A-Z0-9]+', raw).group()
    elif '_' in raw:             # Eg: VanY-D_4_AY489045, dfrB3_1_FM877478
        return raw.split('_')[-1]
    elif re.search('.orf\d*.gene$', raw):   # Eg: EU177504.2.orf0.gene
        return raw.split('.orf')[0]
    elif re.search('.gene\d*$', raw):       # Eg: AY139592.1.gene4
        return raw.split('.gene')[0]
    elif ':' in raw:                        # Eg: (Tmt)DfrB4:FM87748469-305:237
        return raw.split(':')[1].split('-')[0]
    else:
        raise RuntimeError('Do not know how to parse: %s' % raw)


def print_duplicates(fnames):
    """Print information about duplicate accession numbers in files."""
    full_names = []
    for fname in fnames:
        for line in open(fname):
            if line.startswith('>'):
                full_names.append(line.split()[0].strip('>'))

    seen = {}  # dict, for each accession number says where it was first seen
    for i, name in enumerate(full_names):
        acc = parse(name)
        if acc not in seen:
            seen[acc] = i
        else:
            first, current = seen[acc], i
            print('* Accession number %s at position %d was first seen at %d:'
                  % (acc, current + 1, first + 1))
            print('  %6d - %s' % (first, full_names[first]))
            print('  %6d - %s' % (current, full_names[current]))



if __name__ == '__main__':
    main()
