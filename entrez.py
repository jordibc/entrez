"""
Simple interface to the amazing NCBI databases (Entrez).
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
    'link': {'db', 'dbfrom', 'cmd'},
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
    'link': {'id', 'query_key', 'WebEnv', 'retmode', 'idtype', 'linkname',
             'term', 'holding', 'datetype', 'reldate', 'mindate', 'maxdate'},
    'gquery': {},
    'spell': {},
    'citmatch': {}}
# For all the available arguments/parameters, see:
# https://www.ncbi.nlm.nih.gov/books/NBK25499/

# We could have a list of valid databases too, for example from
# https://www.ncbi.nlm.nih.gov/books/NBK25497/table/chapter2.T._entrez_unique_identifiers_ui/
# but it is missing some, like 'nucleotide'.


def equery(tool='search', raw_params='', **params):
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


def eselect(tool, db, elems=None, **params):
    """Use tool on db to select elements and return dict for future queries."""
    # If there are previous elements selected, take them into account.
    if elems and 'WebEnv' in elems:
        params['WebEnv'] = elems['WebEnv']
    if elems and 'QueryKey' in elems:
        params['query_key'] = elems['QueryKey']

    # Use search with usehistory='y' to select the elements.
    if tool == 'search':
        params['usehistory'] = 'y'

    # Keep the values of WebEnv, QueryKey and Count in the elems_new dict.
    elems_new = {}
    for line in equery(tool=tool, db=db, **params):
        for k in ['WebEnv', 'QueryKey', 'Count']:
            if k not in elems_new and f'<{k}>' in line:
                elems_new[k] = re.search(f'<{k}>(\\S+)</{k}>', line).groups()[0]

    assert 'WebEnv' in elems_new and 'QueryKey' in elems_new, \
        f'Expected WebEnv and QueryKey in result of selection: {elems_new}'

    return elems_new


def eapply(tool, db, elems, retmax=500, **params):
    """Yield the results of applying tool on db for the selected elements.

    Apply tool on database db, for the selected elements (referenced
    in dict elems) from a previous query, and yield the output.

    Args:
      tool: E-utility that is used on the selected elements.
      db: Database where the tool is applied.
      elems: Dict with WebEnv and QueryKey of previously selected elements.
      retmax: Chunk size of the reading from the NCBI servers.
      params: Extra parameters to use with the E-utility.
    """
    assert 'WebEnv' in elems and 'QueryKey' in elems, \
        f'Expected WebEnv and QueryKey in elems: {elems}'

    # Ask for the results of using tool over the selected elements, in
    # batches of retmax each.
    for retstart in range(0, int(elems.get('Count', '1')), retmax):
        for line in equery(tool=tool, db=db,
                           WebEnv=elems['WebEnv'], query_key=elems['QueryKey'],
                           retstart=retstart, retmax=retmax, **params):
            yield line


def on_search(term, db, tool, db2=None, **params):
    """Yield the results of querying db with term, and using tool over them.

    Select (search) the elements in database db that satisfy the query
    in term, and yield the output of applying the given tool on them.

    Args:
      term: Query term that selects elements to process later.
      db: Database where the query is done.
      tool: E-utility that is used on the selected elements.
      db2: Database where tool is applied. If None, it's the same as db.
      params: Extra parameters to use with the E-utility.
     """
    # Convenience function, it is used so often.
    elems = eselect(tool='search', db=db, term=term)
    for line in eapply(tool=tool, db=(db2 or db), elems=elems, **params):
        yield line


# Convenient translations.
#
# Many results come as an xml string, and it would be very nice to
# manage them as python dictionaries / lists.

class Nested:
    def __init__(self, obj):
        self.obj = obj

    def __getitem__(self, key):
        if type(self.obj) == list:
            if type(key) == int:
                return Nested(self.obj[key])

            head, *rest = key.split(None, 1)

            obj_next = self.obj[int(head)]

            return Nested(obj_next)[rest[0]] if rest else obj_next

        if key in self.obj:
            return Nested(self.obj[key])

        try:
            head, rest = key.split(None, 1)
            return Nested(self.obj[head])[rest]
        except ValueError:
            raise KeyError(key)

    def __repr__(self):
        return self.obj.__repr__()

    def view(self, print_object=True):
        """Interactive session to get subcomponents of the object."""
        readline_init()

        item = self  # start at the top level (and will select subcomponents)
        path = []  # path to the currently selected subcomponent

        while True:
            obj = item.obj

            if print_object:
                pprint.pprint(obj)

            if type(obj) == dict:
                readline_set_completer(list(obj.keys()))
            elif type(obj) == list:
                readline_set_completer([str(i) for i in range(len(obj))])
            else:
                if path:
                    print('Path to the subcomponent:', ' '.join(path))
                return obj

            print('\nSelection (you can use arrows, tab, Ctrl+r, etc.):', end='')

            choice = input('\n> ')

            if not choice:
                if path:
                    print('Path to the subcomponent:', ' '.join(path))
                return None  # we don't want to output some big component

            path.append(choice)

            readline.clear_history()

            item = Nested(obj)[choice]


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
    """Return the given xml string as a python object."""
    xml_str = xml if type(xml) == str else '\n'.join(xml)

    try:
        obj = xml_node_to_dict(ElementTree.XML(xml_str))
    except ElementTree.ParseError:
        obj = [xml_node_to_dict(ElementTree.XML(x))
               for x in xml_str.splitlines()]
    return Nested(obj)


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
