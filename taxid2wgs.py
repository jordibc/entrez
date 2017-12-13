#!/usr/bin/env python3
"""
Collect and parse NCBI WGS project fasta files from a taxid

Download NCBI WGS fasta files gzipped and process them to generate
a single coherent fasta file.
"""

#
# Useful references at NCBI:
# * Stand-alone BLAST and WGS projects (taxid2wgs.pl info):
#     ftp://ftp.ncbi.nlm.nih.gov/blast/WGS_TOOLS/README_BLASTWGS.txt
# * GenBank WGS Projects:
#     ftp://ftp.ncbi.nih.gov/genbank/wgs/README.genbank.wgs
# * WGS projects browser:
#     https://www.ncbi.nlm.nih.gov/Traces/wgs/
# * WGS projects data:
#     ftp://ftp.ncbi.nlm.nih.gov/sra/wgs_aux/
#

import argparse
from ftplib import FTP, error_temp, error_proto, error_reply
import gzip
import http.client
import os
import re
import sys
import threading
import time

__version__ = '0.1.10'
__date__ = 'Dec 2017'

RETRY_TIMES = [0, 5, 15, 30, 60, 120]
EXCEPTS = (OSError, EOFError, error_temp, error_proto, error_reply)
FTP_SERVER = 'ftp.ncbi.nlm.nih.gov'
FSA_WGS_END = '.fsa_nt.gz'


def resume_info():
    """Print last information about resume option."""
    print('\n\033[94m NOTE\033[90m: You can try to solve any issue and resume'
          '\n\tthe process using the \033[0m-r/--resume\033[90m flag.\033[0m')


def download_file(ftp, filename):
    """Download file while keeping FTP connection alive."""
    def bkg_download():
        """ Aux method to download file in background"""
        with open(filename, 'wb') as file:
            ftp.voidcmd('TYPE I')  # Binary transfer mode
            sckt = ftp.transfercmd('RETR ' + filename)
            while True:
                chunk = sckt.recv(2**25)  # bufsize as a power of 2 (32 MB)
                if not chunk:
                    break
                file.write(chunk)
            sckt.close()

    thrd = threading.Thread(target=bkg_download())
    thrd.start()
    while thrd.is_alive():
        thrd.join(30)  # Seconds to wait to send NOOPs while downloading
        ftp.voidcmd('NOOP')


def dyn_progress():
    """Generator to provide progress of process"""
    states = r'- \ | /'.split()
    while True:
        for state in states:
            yield state


def main():
    """Main entry point to the script."""
    # Argument Parser Configuration
    parser = argparse.ArgumentParser(
        description='Collect NCBI WGS project fasta files from a taxid',
        epilog='%(prog)s -- {}'.format(__date__),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        '-d', '--download',
        action='store_true',
        help='Just download (not parse) the WGS project files'
    )
    parser.add_argument(
        '-e', '--reverse',
        action='store_true',
        help='Reversed (alphabetical) order for processing projects'
    )
    mode = parser.add_mutually_exclusive_group(required=False)
    mode.add_argument(
        '-f', '--force',
        action='store_true',
        help='Force downloading and recreating the final FASTA file in '
             'spite of any previous run. This will clear temporal and output '
             'files but not previous downloads.'
    )
    mode.add_argument(
        '-r', '--resume',
        action='store_true',
        help='Resume downloading without checking the server for every project'
    )
    parser.add_argument(
        '-t', '--taxid',
        action='store',
        metavar='TAXID',
        type=str,
        default='548681',  # Herpesvirus as test taxid
        help='NCBI taxid code to include a taxon and all underneath.'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='produce verbose output  (combine with --debug for further info)'
    )
    parser.add_argument(
        '-V', '--version',
        action='version',
        version='%(prog)s release {} ({})'.format(__version__, __date__)
    )
    parser.add_argument(
        '-x', '--exclude',
        action='store',
        metavar='TAXID',
        type=str,
        default='',
        help='NCBI taxid code to exclude a taxon and all underneath.'
    )

    # Parse arguments
    args = parser.parse_args()
    just_download = args.download
    force = args.force
    resume = args.resume
    reverse = args.reverse
    taxid = args.taxid
    exclude = args.exclude
    verb = args.verbose

    # Program header
    print('\n=-= {} =-= v{} =-= {} =-=\n'.format(
        sys.argv[0], __version__, __date__))

    # Set output and temporal filenames
    if exclude:
        fstfile = 'WGS4taxid' + taxid + '-' + exclude + '.fa'
        tmpfile = 'WGS4taxid' + taxid + '-' + exclude + '.tmp'
    else:
        fstfile = 'WGS4taxid' + taxid + '.fa'
        tmpfile = 'WGS4taxid' + taxid + '.tmp'

    # Get lists of previously downloaded and parsed files
    previous = [entry.name for entry in os.scandir() if entry.is_file()
                and entry.name.endswith(FSA_WGS_END)]
    parsed = []
    if os.path.exists(tmpfile):
        if force:
            os.remove(tmpfile)
        elif just_download:
            parsed_raw = open(tmpfile, 'r').readlines()
            parsed = [proj.rstrip() for proj in parsed_raw]
        elif resume:
            parsed_raw = open(tmpfile, 'r').readlines()
            parsed = [proj.rstrip() for proj in parsed_raw]
            if parsed and not os.path.isfile(fstfile):
                print('\033[91m ERROR!\033[90m Temp file \0330m{}\033[90m '
                      'exists but not the corresponding FASTA file '
                      '\033[91m{}\033[90m.\nPlease correct this or run with '
                      'force flag enabled.'.format(tmpfile, fstfile))
                exit(1)
        else:
            print('\033[91m ERROR!\033[90m Temp file \033[0m{}\033[90m exists '
                  'but resume flag not set.\nPlease correct this or run with '
                  'download, resume or force flag.\033[0m'.format(tmpfile))
            exit(2)
    elif os.path.exists(fstfile):
        if force:
            os.remove(fstfile)
        else:
            print('\033[91m ERROR!\033[90m FASTA file \033[0m{}\033[90m exists'
                  ' (but temporal file missing).\nPlease correct this or run '
                  'with force flag enabled.\033[0m'.format(fstfile))
            exit(3)
    # Display some info
    if verb:
        if force:
            print('\033[94mINFO\033[90m: All cleared by '
                  '\033[93mforce\033[90m flag!\033[0m')
        if just_download:
            print('\033[94mINFO\033[90m: "Just download" mode enabled.\033[0m')
        if reverse:
            print('\033[94mINFO\033[90m: Reversed mode enabled.\033[0m')
    if resume or (just_download and not force):
        print(len(previous), '\033[90mWGS project files are in current '
                             'dir. If any, we won\'t look for them.\033[0m')
        print(len(parsed), '\033[90mWGS projects already parsed. '
                           'If any, we will ignore them.\033[0m')
    sys.stdout.flush()

    # Get WGS project list from taxid and exclude
    conn = http.client.HTTPSConnection('www.ncbi.nlm.nih.gov')
    conn.request(
        'GET', r'/blast/BDB2EZ/taxid2wgs.cgi?INCLUDE_TAXIDS=' + taxid +
               r'&EXCLUDE_TAXIDS=' + exclude
    )
    response = conn.getresponse()
    if verb:
        print('\033[90mNCBI server response result:\033[0m',
              response.status, response.reason)
    data = response.read()
    wgs_projects_raw = data.replace(b'WGS_VDB://',
                                    b'').rstrip().decode().split('\n')
    wgs_projects = [proj for proj in wgs_projects_raw if proj not in parsed]
    if not wgs_projects:
        print('\033[90mNo projects to process!\033[92m All done!\033[0m')
        exit(0)
    # There are projects to process. Go ahead!
    wgs_projects.sort(reverse=reverse)
    print(len(wgs_projects), '\033[90mWGS projects to collect for '
                             'tid\033[0m', taxid, end='')
    if exclude:
        print('\033[90m excluding tid\033[0m', exclude)
    else:
        print('\033[0m')
    sys.stdout.flush()
    basedir = '/sra/wgs_aux/'
    # Append to fasta file (main output) and temporal file (projects done)
    if just_download:
        fstfile = tmpfile = '/dev/null'  # Don't touch the real files
    with open(fstfile, 'a') as wgs, open(tmpfile, 'a') as tmp:
        processed = len(parsed)
        progress = dyn_progress()
        # Looping for projects in the WGS projects to process
        for proj in wgs_projects:
            ftp = None
            downloaded = []
            to_download = []
            skipped = True
            if resume:
                downloaded = [f for f in previous if f.startswith(proj)]
                if downloaded:
                    if verb:
                        print('\033[90m [Project\033[0m %s\033[90m '
                              'seems in disk. Skipping...]\033[0m' % proj)
                    to_download = downloaded
            if not downloaded:
                if verb:
                    print('\033[90m{} of {}: Process WGS \033[0m{}\033[90m '
                          'project...\033[0m'.format(processed + 1,
                                                     len(wgs_projects), proj),
                          end='')
                    sys.stdout.flush()
                filenames = []
                error = None
                for retry_time in RETRY_TIMES:
                    if retry_time:
                        print('\n\033[90m Retrying in %s seconds...\033[0m'
                              % retry_time, end='')
                        sys.stdout.flush()
                    time.sleep(retry_time)
                    try:
                        ftp = FTP(FTP_SERVER, timeout=30)
                        ftp.set_debuglevel(0)
                        ftp.login()
                        ftp.cwd(os.path.join(basedir, proj[0:2],
                                             proj[2:4], proj))
                        filenames = ftp.nlst()
                    except EXCEPTS as err:
                        print('\033[93m PROBLEM!\033[0m', end='')
                        error = err
                    except KeyboardInterrupt:
                        print('\033[90m User\033[93m interrupted!\033[0m')
                        resume_info()
                        exit(9)
                    else:
                        break
                else:  # Too many problems, quit
                    print('\033[91m FAILED!\033[90m '
                          'Exceeded number of attempts!\033[0m')
                    print('\033[90mError message:\033[0m', error)
                    resume_info()
                    exit(5)
                to_download = [file for file in filenames
                               if file.endswith(FSA_WGS_END)]
            # Looping for files in the WGS project
            for filename in to_download:
                # Check for already downloaded
                if not force and os.path.isfile(filename):
                    if verb:
                        print('\033[90m[%s already downloaded]\033[0m' %
                              filename, end=' ')
                else:
                    error = None
                    for retry_time in RETRY_TIMES:
                        if retry_time:
                            print('\n\033[90m Retrying in %s seconds...\033[0m'
                                  % retry_time, end='')
                            sys.stdout.flush()
                        time.sleep(retry_time)
                        try:
                            if retry_time:
                                ftp = FTP(FTP_SERVER, timeout=30)
                                ftp.login()
                                ftp.cwd(os.path.join(basedir, proj[0:2],
                                                     proj[2:4], proj))
                            download_file(ftp, filename)
                            # ftp.retrbinary('RETR ' + filename,
                            #                open(filename, 'wb').write)
                        except EXCEPTS as err:
                            print('\033[93m PROBLEM!\033[0m', end='')
                            error = err
                        except KeyboardInterrupt:
                            print('\033[90m User\033[93m interrupted!\033[0m')
                            resume_info()
                            try:  # Avoid keeping in disk a corrupt file
                                os.remove(filename)
                            except OSError:
                                pass
                            exit(9)
                        else:
                            break
                    else:  # Too many problems, quit
                        try:  # Avoid keeping in disk a corrupt file
                            os.remove(filename)
                        except OSError:
                            pass
                        print('\033[91m FAILED!\033[90m '
                              'Exceeded number of attempts!\033[0m')
                        print('\033[90mError message:\033[0m', error)
                        resume_info()
                        exit(5)
                    skipped = False
                # Decompress, parse and update headers if needed
                if just_download:
                    continue  # Avoid further processing
                with gzip.open(filename, 'rt') as filegz:
                    all_lines = []
                    try:
                        all_lines = filegz.readlines()
                        if not all_lines:
                            raise EOFError
                    except EOFError:
                        print('\n\033[91m FAILED!\033[90m Unexpected EOF '
                              'while parsing file \033[0m{}\033[90m. '
                              'Is it corrupted?\033[0m'.format(filename))
                        resume_info()
                        exit(4)
                    line1 = all_lines[0]
                    # Check fasta-read header format
                    if proj in line1[0:7]:  # New format: just save all
                        wgs.writelines(all_lines)
                    else:  # Old format: parse the headers
                        pattern = re.compile(r'(%s(?:\d){5,8}\.\d)\|([\w\W]*)$'
                                             % proj)
                        match = re.search(pattern, line1)
                        accession = match.group(1)
                        description = match.group(2).strip()
                        wgs.write('>%s %s\n' % (accession, description))
                        try:
                            for line in all_lines:
                                if line[0] != '>':  # Sequence line
                                    wgs.write(line)
                                else:  # Header line to parse
                                    match = re.search(pattern, line)
                                    accession = match.group(1)
                                    description = match.group(2).strip()
                                    wgs.write('>%s %s\n'
                                              % (accession, description))
                        except EOFError:
                            print('\n\033[91m FAILED!\033[90m Unexpected EOF '
                                  'while parsing file \033[0m{}\033[90m. '
                                  'Is it corrupted?\033[0m'.format(filename))
                            resume_info()
                            exit(3)
            # Project is done: update temporal file and console output
            if ftp:
                try:
                    ftp.quit()
                except EXCEPTS:
                    try:
                        ftp.close()
                    except EXCEPTS:
                        pass
            tmp.write(proj + '\n')
            tmp.flush()
            processed += 1
            if verb:
                print('\033[92m OK! \033[0m')
            else:
                if processed % 1 == 0:
                    print('\r\033[95m{}\033[0m [{:.2%}]\033[90m'.format(
                        next(progress), processed / len(wgs_projects_raw)),
                        end='')
                    if skipped:
                        print(' Skipping download. Parsing...\033[0m', end='')
                    elif just_download:
                        print(' Just downloading...\033[0m          ', end='')
                    else:
                        print(' Downloading and parsing...\033[0m   ', end='')
            sys.stdout.flush()
    if just_download:
        print('\033[92mAll downloaded! \033[0m')
    else:
        print('\033[92mAll OK! \033[0m')
        try:  # Remove temporal file. Not needed anymore.
            os.remove(tmpfile)
        except OSError:
            print('\033[93m WARNING!\033[90m Failed to remove temporal file '
                  '\033[0m{}\033[90m!\033[0m'.format(tmpfile))
            exit(5)


if __name__ == '__main__':
    main()
