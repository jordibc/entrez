"""
Simple python interface to the NCBI databases (Entrez).

See https://www.ncbi.nlm.nih.gov/books/NBK25500/
"""

# Useful references (at https://www.ncbi.nlm.nih.gov/books):
# * Converting accession numbers:
#     /NBK25498/#chapter3.Application_2_Converting_access
# * Retrieving large datasets:
#     /NBK25498/#chapter3.Application_3_Retrieving_large
# * E-utilities:
#     /NBK25497/#chapter2.The_Nine_Eutilities_in_Brief

import re
import urllib.parse, urllib.request, urllib.error

from itertools import groupby
from xml.etree import ElementTree

import pprint
import readline


EMAIL = None
API_KEY = None

_tools = {  # valid tools
    'info', 'search', 'post', 'summary', 'fetch', 'link', 'gquery', 'spell',
    'citmatch'}

_required = {  # required arguments for each tool
    'info': {},
    'search': {'db', 'term'},
    'post': {'db', 'id'},
    'summary': {'db'},
    'fetch': {'db'},
    'link': {'db', 'dbfrom'},
    'gquery': {'term'},
    'spell': {'db', 'term'},
    'citmatch': {'db', 'rettype' 'bdata'}}

_optional = {  # optional arguments for each tool
    'info': {'db', 'version', 'retmode'},
    'search': {'usehistory', 'WebEnv', 'query_key', 'retstart', 'retmax',
               'rettype', 'retmode', 'sort', 'field', 'idtype', 'datetype',
               'reldate', 'mindate', 'maxdate'},
    'post': {'WebEnv'},
    'summary': {'id', 'query_key', 'WebEnv', 'retstart', 'retmax', 'rettype',
                'retmode', 'version'},
    'fetch': {'id', 'query_key', 'WebEnv', 'retstart', 'retmax', 'rettype',
              'retmode', 'strand', 'seq_start', 'seq_stop', 'complexity'},
    'link': {'id', 'query_key', 'WebEnv', 'retmode', 'idtype', 'linkname', 'cmd',
             'term', 'holding', 'datetype', 'reldate', 'mindate', 'maxdate'},
    'gquery': {},
    'spell': {},
    'citmatch': {}}
# For all the available arguments/parameters, see:
# https://www.ncbi.nlm.nih.gov/books/NBK25499/

# We could have a list of valid databases too, for example from
# https://www.ncbi.nlm.nih.gov/books/NBK25497/table/chapter2.T._entrez_unique_identifiers_ui/
# but it is missing some, like 'nucleotide'.


def query(tool='search', raw_params='', **params):
    """Yield the response of a query with the given tool."""
    # First make some basic checks.
    assert tool in _tools, \
        f'Invalid web tool "{tool}". Valid tools are: {_tools}'
    for p in _required[tool]:
        assert p in params, f'Missing required argument: {p}'
    for p in params:
        assert p in _required[tool] | _optional[tool] | {'api_key', 'email'}, \
            f'Unknown argument: {p}'
    # We could check more and better than this, but it's probably unnecessary.

    # Make a POST request and yield the lines of the response.
    url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/e{tool}.fcgi'

    if not 'email' in params and not 'email' in raw_params and EMAIL:
        params['email'] = EMAIL
    if not 'api_key' in params and not 'api_key' in raw_params and API_KEY:
        params['api_key'] = API_KEY

    data = (urllib.parse.urlencode(params) + raw_params).encode('ascii')
    try:
        for line_bytes in urllib.request.urlopen(url, data):
            yield line_bytes.decode('ascii', errors='ignore').rstrip()
    except urllib.error.HTTPError as e:
        raise RuntimeError(f'On POST request to {url} with {data}: {e}')


def select(tool, db, previous=None, **params):
    """Use tool on db to select elements and return dict for future queries."""
    # If there are previous elements selected, take them into account.
    if previous and 'WebEnv' in previous:
        params['WebEnv'] = previous['WebEnv']
    if previous and 'QueryKey' in previous:
        params['query_key'] = previous['QueryKey']

    # Use search with usehistory='y' to select the elements.
    if tool == 'search':
        params['usehistory'] = 'y'

    # Keep the values of WebEnv, QueryKey and Count in the selections dict.
    selections = {}
    for line in query(tool=tool, db=db, **params):
        for k in ['WebEnv', 'QueryKey', 'Count']:
            if k not in selections and f'<{k}>' in line:
                matches = re.search(f'<{k}>(\\S+)</{k}>', line)
                selections[k] = matches.groups()[0]

    assert 'WebEnv' in selections and 'QueryKey' in selections, \
        f'Expected WebEnv and QueryKey in result of selection: {selections}'

    return selections


def apply(tool, db, selections, retmax=500, **params):
    """Yield the results of applying tool on db for the selected elements.

    Apply tool on database db, for the selected elements (referenced
    in dict selections) from a previous query, and yield the output.

    Args:
      tool: E-utility that is used on the selected elements.
      db: Database where the tool is applied.
      selections: Dict with WebEnv and QueryKey of previously selected elements.
      retmax: Chunk size of the reading from the NCBI servers.
      params: Extra parameters to use with the E-utility.
    """
    assert 'WebEnv' in selections and 'QueryKey' in selections, \
        f'Expected WebEnv and QueryKey in selections: {selections}'

    # Ask for the results of using tool over the selected elements, in
    # batches of retmax each.
    for retstart in range(0, int(selections.get('Count', '1')), retmax):
        yield from query(tool=tool, db=db,
                         WebEnv=selections['WebEnv'],
                         query_key=selections['QueryKey'],
                         retstart=retstart, retmax=retmax, **params)


def on_search(term, db, tool, dbfrom=None, **params):
    """Yield the results of searching db with term, and using tool over them.

    Select (search) the elements in database dbfrom (or db if not
    specified) that satisfy the query in term, and yield the output of
    applying the given tool on them.

    Args:
      term: Query term that selects elements to process later.
      db: Database where tool is applied.
      tool: E-utility that is used on the selected elements.
      dbfrom: Database where the query is done. If None, it's the same as db.
      params: Extra parameters to use with the E-utility.
    """
    # Convenience function, it is used so often.
    selections = select(tool='search', db=(dbfrom or db), term=term)
    yield from apply(tool=tool, db=db, selections=selections, **params)


# Convenient translations.
#
# Many results come as an xml string, and it would be very nice to
# manage them as python dictionaries / lists.

class Nest:
    def __init__(self, obj):
        assert type(obj) in [dict, list], 'Can only Nest() dict or list.'
        self.obj = obj

    def __getitem__(self, key):
        if type(self.obj) == list:
            if type(key) == int:
                return wrap(self.obj[key])

            try:
                head, *rest = key.split(None, 1)
                item = wrap(self.obj[int(head)])
                return item[rest[0]] if rest else item
            except ValueError:
                raise KeyError(key)
        else:  # dict
            if key in self.obj:
                # In the unlikely case that we have a key with whitespace.
                return wrap(self.obj[key])

            try:
                head, *rest = key.split(None, 1)
                item = wrap(self.obj[head])
                return item[rest[0]] if rest else item
            except (ValueError, KeyError):
                raise KeyError(key)

    def __iter__(self):
        if type(self.obj) == list:
            for obj in self.obj:
                yield wrap(obj)
        else:
            for key, value in self.obj.items():
                yield key, wrap(value)

    def __eq__(self, value):
        return (type(value) in [dict, list, Nest] and
                len(self) == len(value) and
                all(x == y for x, y in zip(self, wrap(value))))

    def __repr__(self):
        return repr(self.obj)

    def __len__(self):
        return len(self.obj)

    def keys(self):
        if type(self.obj) == list:
            return list(range(len(self.obj)))
        else:
            return list(self.obj.keys())

    def values(self):
        if type(self.obj) == list:
            return self.obj
        else:
            return list(self.obj.values())

    def items(self):
        return zip(self.keys(), self.values())

    def view(self, width=120, depth=4, compact=True, sort_dicts=False):
        """Interactive session to get subcomponents of the object."""
        readline_init()

        obj = self.obj  # start at the top level (and will select subcomponents)
        path = []  # path to the currently selected subcomponent

        while True:
            if type(obj) == dict:
                readline_set_completer(list(obj.keys()))
            else:  # list
                readline_set_completer([str(i) for i in range(len(obj))])

            while True:
                print('\nSelection:')

                try:
                    prefix = "['%s'] " % ' '.join(path)
                    choice = input("%s> " % (prefix if path else ''))
                except (EOFError, KeyboardInterrupt):
                    print()
                    return

                if choice:
                    break

                print()
                pprint.pprint(obj, width=width, depth=depth, compact=compact,
                              sort_dicts=sort_dicts)

            try:
                item = Nest(obj)[choice]
                path.append(choice)

                if type(item) != Nest:  # we are done, no more nesting
                    print("Path: ['%s']" % ' '.join(path))
                    print('Value:', item)
                    return

                obj = item.obj
            except KeyError:
                print(f'\nNonexistent key: {choice}')
                print('You can select a key with the arrows, tab, Ctrl+r, etc. '
                      'Exit with Ctrl+d. View current selection with Enter.')

            readline.clear_history()


def wrap(x):
    """Return object x, but "wrapped" as Nest if it makes sense."""
    return Nest(x) if type(x) in [dict, list] else x


def readline_init():
    """Initialize readline."""
    readline.parse_and_bind('tab: complete')
    readline.parse_and_bind('set show-all-if-ambiguous on')

    readline.set_completer_delims('')  # use full sentence, not just words
    readline.set_auto_history(False)  # do not add new lines to history


def readline_set_completer(names):
    for name in names:
        readline.add_history(name)  # so one can scroll and search them

    def completer(text, state):
        matches = [name for name in names if text.lower() in name.lower()]
        return matches[state] if state < len(matches) else None

    readline.set_completer(completer)


def read_xml(xml):
    """Return the given xml string(s) as a python object."""
    # Used to read a typical Entrez response, which can have several xmls.
    xml_str = xml if type(xml) == str else '\n'.join(xml)

    # Separate all xmls (even if typically there is only one).
    xmls = []
    start, end = 0, xml_str.find('\n<?xml')
    while end != -1:
        xmls.append(xml_str[start:end])
        start, end = end + 1, xml_str.find('\n<?xml', end + 1)
    xmls.append(xml_str[start:])

    obj = [xml_node_to_dict(ElementTree.XML(x)) for x in xmls]
    return Nest(obj[0] if len(obj) == 1 else obj)


def xml_node_to_dict(node):
    """Return a dict with the contents of the given xml node."""
    # If the node has attributes, we'll keep them with a "@" in front.
    subdict = {'@'+k: v for k, v in node.attrib.items()}

    tag = node.tag
    tags = [n.tag for n in node]  # all tags in children nodes
    ntags = len(set(tags))  # number of different tags in children

    if len(tags) == 0:  # no children -> add its text
        if len(subdict) == 0:
            return {tag: node.text or ''}
        else:
            return {tag: dict(subdict, text=(node.text or ''))}
    elif len(tags) == ntags:  # all tags are different -> add a dict
        for n in node:
            subdict.update(xml_node_to_dict(n))  # add content from subnodes
        return {tag: subdict}
    elif ntags == 1:  # all tags are the same -> add a list
        if len(subdict) == 0:
            return {tag: [xml_node_to_dict(n) for n in node]}
        else:
            return {tag: dict(subdict,
                              children=[xml_node_to_dict(n) for n in node])}
    else:  # some tags are the same and others aren't... what the heck
        nodes = sorted((n for n in node), key=lambda n: n.tag)

        for gtag, group_tag in groupby(nodes, lambda n: n.tag):
            nodes_tag = list(group_tag)  # don't exhaust the iterator

            if len(nodes_tag) == 1:
                subdict.update(xml_node_to_dict(nodes_tag[0]))
            else:
                subdict.update({(gtag+'-group'):
                                [xml_node_to_dict(n) for n in nodes_tag]})
        return {tag: subdict}
