#!/usr/bin/env python3

"""
Make a blast query using the NCBI web API.
"""

# Based on web_blast.pl from NCBI.
# For more info on the api, see https://ncbi.github.io/blast-cloud/dev/api.html

import sys
import re
import time
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter as fmt
import requests


def main():
    args = get_args()

    # The "query" will be the contents of all the given fasta files.
    fastas = ''.join(open(fname).read() for fname in args.fasta_files)

    url_noquery = (f'{args.urlbase}?CMD=Put&PROGRAM={args.program}'
                   f'&DATABASE={args.database}&QUERY=')

    print(f'Making request to {url_noquery}[...]')  # show url without the query

    req_query = requests.post(url_noquery + requests.utils.quote(fastas))

    rid = get_value(req_query, 'RID')  # request id
    rtoe = get_value(req_query, 'RTOE')  # estimated time to completion

    print(f'Got a request id {rid}. Estimated wait of {rtoe} s. Waiting.')
    time.sleep(int(rtoe))  # wait for search to complete

    url_info = f'{args.urlbase}?CMD=Get&FORMAT_OBJECT=SearchInfo&RID={rid}'
    print(f'Checking every {args.wait} s the status at {url_info}')

    while True:
        print('.', end='')  # just to show the passage of time
        sys.stdout.flush()

        req_info = requests.get(url_info)

        status = get_value(req_info, 'Status')

        if status == 'READY':
            print('\nThe results are ready!')
            break
        elif status == 'WAITING':
            time.sleep(args.wait)
        else:
            print()
            sys.exit(f'Finished with status: {status}')

    url_results = f'{args.urlbase}?CMD=Get&FORMAT_TYPE={args.format}&RID={rid}'
    print(f'Retrieving results from {url_results}')

    results = requests.get(url_results).text

    if args.output is not None:
        open(args.output, 'wt').write(results)
        print(f'Results written to: {args.output}')
    else:
        print(results)


def get_args():
    """Return the parsed command line arguments."""
    parser = ArgumentParser(description=__doc__, formatter_class=fmt)

    add = parser.add_argument  # shortcut
    add('fasta_files', metavar='FASTA_FILE', nargs='+',
        help='fasta file(s) with sequences to query')
    add('-p', '--program', default='blastn', help='blast program to use',
        choices=['blastn', 'blastp', 'blastx', 'tblastn', 'tblastx'])
    add('-d', '--database', default='nr',
        help='database to query ("nr", "refseq_representative_genomes", etc.)')
    add('-f', '--format', default='Text', help='format for the output',
        choices=['Text', 'Tabular', 'XML', 'XML2', 'HTML', 'JSON2'])
    add('-o', '--output', help='if given, file where to write the results')
    add('--wait', type=int, default=5, help='seconds to wait between checks')
    add('--urlbase', default='https://blast.ncbi.nlm.nih.gov/blast/Blast.cgi',
        help='base url where to contact the blast web api')

    return parser.parse_args()


def get_value(response, key):
    # All the values we care for appear in the responses as "<key> = <value>".
    return re.findall(f'{key} ?= ?(.*)', response.text)[0]



if __name__ == '__main__':
    main()
