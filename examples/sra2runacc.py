#!/usr/bin/env python3

"""
Use Entrez utilities to get all the run accession numbers for a SRA study.

Such run accession numbers can be passed, for example, to a NCBI SRA Toolkit
utility like fastq-dump or fasterq-dump to retrieve all the FASTQ files of
the different samples in the SRA study.
"""

# Useful references:
# * NCBI SRA Toolkit docs: https://www.ncbi.nlm.nih.gov/sra/docs/
# * NCBI SRA Toolkit repo: https://github.com/ncbi/sra-tools
# * NCBI SRA Toolkit wiki: https://github.com/ncbi/sra-tools/wiki

import sys
import argparse
import re

sys.path.append('..')
import entrez as ez


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('sra', metavar='SRAid', help='SRA identifier')
    args = parser.parse_args()

    for line in ez.on_search(db='sra', term=args.sra, tool='summary'):
        if 'Name="Runs"' in line:
            acc = re.search('acc=\"(?P<acc>\w+[0-9]+)\"', line).group('acc')
            print(acc)



if __name__ == '__main__':
    main()
