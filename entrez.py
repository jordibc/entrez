"""Simple interface to the amazing NCBI databases (Entrez).

equery(tool[, ...]) - Yield the response of a query with the given tool.
eselect(tool, db[, elems, ...]) - Return a dict that references the elements
    selected with tool over database db.
eapply(tool, db, elems[, retmax, ...]) - Yield the response of applying
    a tool on db for the selected elements.
on_search(db, term, tool[, db2, ...]) - Yield the response of applying a
    tool over the results of a search query.

Examples of use:

* Fetch information for SNP with id 3000, as in the example of
  https://www.ncbi.nlm.nih.gov/projects/SNP/SNPeutils.htm

  for line in equery(tool='fetch', db='snp', id='3000'):
      print(line)

* Get a summary of nucleotides related to accession numbers
  NC_010611.1 and EU477409.1

  for line in on_search(db='nucleotide',
                        term='NC_010611.1[accn] OR EU477409.1[accn]',
                        tool='summary'):
      print(line)

"""

#
# Useful references (at https://www.ncbi.nlm.nih.gov/books):
# * Converting accession numbers:
#     /NBK25498/#chapter3.Application_2_Converting_access
# * Retrieving large datasets:
#     /NBK25498/#chapter3.Application_3_Retrieving_large
# * E-utilities:
#     /NBK25497/#chapter2.The_Nine_Eutilities_in_Brief
#

from re import search
from urllib.parse import urlencode
from urllib.request import urlopen
from itertools import groupby
from xml.etree import ElementTree


_valid_tools = 'info search post summary fetch link gquery citmatch'.split()
_valid_params = ('db dbfrom term id cmd linkname usehistory query_key WebEnv '
                 'rettype retmode retstart retmax api_key').split()

API_KEY = None


def equery(tool='search', raw_params='', **params):
    """Yield the response of a query with the given tool."""
    # First make some basic checks.
    assert tool in _valid_tools, 'Invalid web tool: %s' % tool
    for k in params:
        assert k in _valid_params, 'Unknown parameter: %s' % k
    # TODO: we could really check better than this...

    # Make a POST request and yield the lines of the response.
    url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/e%s.fcgi' % tool

    if not 'api_key' in params and not 'api_key' in raw_params and API_KEY:
        params['api_key'] = API_KEY

    data = (urlencode(params) + raw_params).encode('ascii')
    for line_bytes in urlopen(url, data):
        yield line_bytes.decode('ascii', errors='ignore').rstrip()


def eselect(tool, db, elems=None, **params):
    """Use tool on db to select elements and return dict for future queries."""
    # If there are previous elements selected, take them into account.
    if elems and 'WebEnv' in elems:
        params['WebEnv'] = elems['WebEnv']
    if elems and 'QueryKey' in elems:
        params['query_key'] = elems['QueryKey']

    # Use tool with usehistory='y' to select the elements,
    # and keep the values of WebEnv, QueryKey and Count in the elems_new dict.
    elems_new = {}
    for line in equery(tool=tool, usehistory='y', db=db, **params):
        for k in ['WebEnv', 'QueryKey', 'Count']:
            if k not in elems_new and '<%s>' % k in line:
                elems_new[k] = search('<%s>(\S+)</%s>' % (k, k), line).groups()[0]
    return elems_new


def eapply(tool, db, elems, retmax=500, **params):
    """Yield the results of applying tool on db for the selected elements.

    For the selected elements (referenced in dict elems) from a previous query
    apply tool on database db, and yield the output.

    Args:
      tool: E-utility that is used on the selected elements.
      db: Database where the tool is applied.
      elems: Dict with WebEnv and QueryKey of previously selected elements.
      retmax: Chunk size of the reading from the NCBI servers.
      params: Extra parameters to use with the E-utility.
    """
    # Ask for the results of using tool over the selected elements, in
    # batches of retmax each.
    for retstart in range(0, int(elems.get('Count', '1')), retmax):
        for line in equery(tool=tool, db=db,
                           WebEnv=elems['WebEnv'], query_key=elems['QueryKey'],
                           retstart=retstart, retmax=retmax, **params):
            yield line


def on_search(db, term, tool, db2=None, **params):
    """Yield the results of querying db with term, and using tool over them.

    Select (search) the elements in database db that satisfy the query
    in term, and yield the output of applying the given tool on them.

    Args:
      db: Database where the query is done.
      term: Query term that selects elements to process later.
      tool: E-utility that is used on the selected elements.
      db2: Database where tool is applied. If None, it's the same as db.
      params: Extra parameters to use with the E-utility.
     """
    # Convenience function, it is used so often.
    for line in eapply(elems=eselect(tool='search', db=db, term=term),
                       db=(db2 or db), tool=tool, **params):
        yield line


# Convenient translations.
#
# Many results come as a xml string, and it would be very nice to
# manage them as python dictionaries.

def read_xml(xml_str):
    """Return the given xml string as a dictionary."""
    return xml_node_to_dict(ElementTree.XML(xml_str))


def xml_node_to_dict(node):
    """Return a dict with the contents of the given xml node."""
    # If the node has attributes, we'll keep them with a "@" in front.
    subdict = {'@'+k: v for k, v in node.attrib.items()}

    tag = node.tag
    tags = [n.tag for n in node]  # all tags in children nodes
    ntags = len(set(tags))  # number of different tags in children

    if len(tags) == 0:  # no children
        if len(subdict) == 0:
            return {tag: node.text or ''}
        else:
            return {tag: dict(subdict, text=(node.text or ''))}
    elif len(tags) == ntags:  # all tags are different
        for n in node:
            subdict.update(xml_node_to_dict(n))  # add content from subnodes
        return {tag: subdict}
    elif ntags == 1:  # all tags are the same
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
