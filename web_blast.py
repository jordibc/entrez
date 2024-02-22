#!/usr/bin/env python3

"""
Make a blast query using the NCBI web API.

Based on web_blast.pl from NCBI, which is public domain.
For more info on the api, see https://ncbi.github.io/blast-cloud/dev/api.html

Please do not submit or retrieve more than one request every two seconds.

Results will be kept at NCBI for 24 hours. For best batch performance, they
recommend that you submit requests after 20:00 EST (1:00 GMT) and retrieve
results before 5:00 EST (10:00 GMT).
"""

import sys
import re
import time
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter as fmt
import requests


def main():
    args = get_args()

    # The "query" will be the contents of all the given fasta files.
    fastas = ''.join(open(fname).read() for fname in args.fasta_files)

    replacements = {'megablast': 'blastn&MEGABLAST=on',
                    'rpsblast': 'blastp&SERVICE=rpsblast'}
    program_str = replacements.get(args.program, args.program)

    url_noquery = (f'{args.urlbase}?CMD=Put&PROGRAM={program_str}'
                   f'&DATABASE={args.database}&QUERY=')

    print(f'Making request to {url_noquery}[...]')  # show url without the query

    req_query = requests.post(url_noquery + requests.utils.quote(fastas))

    rid = re.findall('RID = (.*)', req_query.text)[0]  # request id
    rtoe = re.findall('RTOE = (.*)', req_query.text)[0]  # estimated wait time

    print(f'Got a request id {rid}. Estimated wait of {rtoe} s. Waiting.')
    time.sleep(int(rtoe))  # wait for search to complete

    url_info = f'{args.urlbase}?CMD=Get&FORMAT_OBJECT=SearchInfo&RID={rid}'
    print(f'Checking every {args.wait} s the status at {url_info}')

    check_periodically(url_info, args.wait)  # check until the results are ready

    url_results = f'{args.urlbase}?CMD=Get&FORMAT_TYPE={args.format}&RID={rid}'
    print(f'Retrieving results from {url_results}')

    results = requests.get(url_results).text.strip()  # get the results

    # Clear the text for certain formats that return ugly text.
    if args.format == 'Tabular':  # the actual result is between <PRE></PRE>
        results = re.findall('<PRE>(.*)</PRE>', results, re.S)[0].strip()
    elif args.format == 'Text':  # the actual result is just after <PRE>
        results = re.findall('<PRE>(.*)', results, re.S)[0].strip()

    # Save to file or print on screen the results.
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
        choices=['blastn', 'blastp', 'blastx', 'tblastn', 'tblastx',
                 'megablast', 'rpsblast'])
    add('-d', '--database', default='nr',
        help='database to query ("nr", "refseq_representative_genomes", etc.)')
    add('-f', '--format', default='Text', help='format for the output',
        choices=['Text', 'Tabular', 'XML', 'XML2', 'HTML', 'JSON2'])
    add('-o', '--output', help='if given, file where to write the results')
    add('--wait', type=int, default=5, help='seconds to wait between checks')
    add('--urlbase', default='https://blast.ncbi.nlm.nih.gov/blast/Blast.cgi',
        help='base url where to contact the blast web api')

    return parser.parse_args()


def check_periodically(url, wait=5):
    """Keep checking the status from the given url until we have results."""
    status = None
    while status != 'READY':
        print('.', end='')  # just to show the passage of time
        sys.stdout.flush()

        status = re.findall('Status=(.*)', requests.get(url).text)[0]

        if status == 'WAITING':
            time.sleep(wait)
        elif status != 'READY':
            print()
            sys.exit(f'Finished with status: {status}')

    print('\nThe results are ready!')



if __name__ == '__main__':
    main()
