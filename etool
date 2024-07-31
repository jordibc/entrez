#!/usr/bin/env python3

"""
Query NCBI databases with the E-utilities (Entrez tools) from the command line.
"""

import sys
from argparse import ArgumentParser
import json

import entrez as ez


def main():
    args = get_args()

    non_tool_args = {'tool', 'on_search', 'parse_xml',
                     'email', 'api_key', 'output'}
    tool_args = {k: v for k, v in args._get_kwargs()
                 if k not in non_tool_args and v is not None}

    out = sys.stdout if not args.output else open(args.output, 'wt')

    # Initialize entrez (email and api key).
    if args.email:
        ez.EMAIL = args.email

    if args.api_key:
        ez.API_KEY = args.api_key

    # Give some extra information (unless we write to a file or similar).
    if out.isatty():
        xtra_info = 'on the results of a search, ' if args.on_search else ''
        print(f"Applying e-tool '{args.tool}' {xtra_info}with {tool_args}")

    try:
        # Query the NCBI databases.
        if not args.on_search:  # normal case
            result = ez.query(tool=args.tool, **tool_args)
        else:  # apply tool on the results of a search (of term in db)
            assert 'term' in tool_args, '--on-search requires --term'
            assert 'db' in tool_args, '--on-search requires --db'
            result = ez.on_search(tool=args.tool, **tool_args)

        # Output the resulting data.
        if not args.parse_xml:  # normal case
            for line in result:
                out.write(line + '\n')
        else:
            parsed = ez.read_xml(result)
            if out.isatty():
                print('\nResults parsed. '
                      'You can select a key with the arrows, tab, Ctrl+r, etc. '
                      'Exit with Ctrl+d. View current selection with Enter.')
                parsed.view()  # interactive view
            else:
                out.write(json.dumps(parsed.obj, indent=2))

    except (KeyboardInterrupt, AssertionError) as e:
        sys.exit(e)


def get_args():
    "Return the parsed command line arguments."
    parser = ArgumentParser(description=__doc__)
    add = parser.add_argument  # shortcut

    add('tool', default='search', choices=ez._tools, help='e-tool to call')
    add('--on-search', action='store_true', help='the tool applies to the results of a search')
    add('--parse-xml', action='store_true', help='try to parse xml output (interactive view)')
    add('--email', help='email of the user making the request')
    add('--api-key', help='API key to pass in the requests')
    add('--output', '-o', help='output file (if not given, use stdout)')

    arguments = sorted(set.union(*ez._required.values(),
                                 *ez._optional.values()))
    for arg in arguments:
        add('--' + arg)

    return parser.parse_args()



if __name__ == '__main__':
    main()
