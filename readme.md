# Entrez - Call the NCBI E-utilities from Python

A simple Python interface to **query the biological databases** kept
at the NCBI.

It uses the [Entrez Programming
Utilities](https://www.ncbi.nlm.nih.gov/books/NBK25497/)
(*E-utilities*), nine server-side programs that access the Entrez
query and database system at the National Center for Biotechnology
Information (NCBI). They provide a structured interface to the Entrez
system, which currently includes 38 databases covering a variety of
biomedical data, including nucleotide and protein sequences, gene
records, three-dimensional molecular structures, and the biomedical
literature.

The main function (and the only essential one) is:

* `equery(tool[, ...])` - yields the response of a query with the given tool

The function `eselect` makes a selection of elements on the server,
that can be referenced later for future queries (instead of
downloading a long list of ids that then we would have to send to the
server again). The function `eapply` can then run a tool using a
previous selection of elements (which can be done with `equery` too,
but `eapply` has a simpler syntax):

* `eselect(tool, db[, ...])` - returns a dict that references the elements
   selected with tool over database db
* `eapply(tool, db, selections[, retmax, ...])` - yields the response of
   applying a tool on db for the selected elements

Finally, `on_search` is a convenience function that combines the
results of a `eselect` on an `eapply`, which is a very common case.

* `on_search(term, db, tool[, db2, ...])` - yields the response of applying a
   tool over the results of a search query (of term in database db)

The data often comes as xml. For convenience, there is also the
function `read_xml` that converts it to a python object closely
resembling the original structure of the data.


## Installation

You can run from this directory without installing anything, or simply
put `entrez.py` in a place where your python interpreter can find it
(for example, you can add this directory to your
[PYTHONPATH](https://docs.python.org/3/using/cmdline.html#envvar-PYTHONPATH)).

Really. There is no need to `pip install` anything (but if you want,
you can `pip install -e .`). Everything is in just one file.


## Examples

Fetch information for SNP with id 3000, as in the example at
https://www.ncbi.nlm.nih.gov/projects/SNP/SNPeutils.htm:

```py
import entrez as ez

for line in ez.equery(tool='fetch', db='snp', id='3000'):
    print(line)  # or:  print(ez.read_xml(line))  for nicer output
```

Get a summary of nucleotides related to accession numbers
`NC_010611.1` and `EU477409.1`:

```py
import entrez as ez

for line in ez.on_search(term='NC_010611.1[accn] OR EU477409.1[accn]',
                         db='nucleotide', tool='summary'):
    print(line)
```

Download to file ``chimp.fna`` all chimpanzee mRNA sequences in FASTA
format (our version of the [sample application
3](https://www.ncbi.nlm.nih.gov/books/NBK25498/#chapter3.Application_3_Retrieving_large)):

```py
import entrez as ez

with open('chimp.fna', 'w') as fout:
    for line in ez.on_search(term='chimpanzee[orgn] AND biomol mrna[prop]',
                             db='nucleotide', tool='fetch', rettype='fasta'):
        fout.write(line + '\n')
```

In the [examples](examples) directory, there is a program
[sample_applications.py](examples/sample_applications.py) that shows
how the [sample applications of the
E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25498) would look
like with this interface.

There are also some little programs: [acc2gi.py](examples/acc2gi.py)
uses the library to convert accession numbers into GIs, and
[sra2runacc.py](examples/sra2runacc.py) uses entrez to get all the run
accession numbers for a given SRA study.


## Email and API keys

The NCBI now asks for all requests to include `email` as a parameter,
with the email address of the user making the request (see their
"[General Usage
Guidelines](https://www.ncbi.nlm.nih.gov/books/NBK25499/)" for
example).

You can pass it to any of the functions in this module as an argument
(for example, `equery(..., email='me@here.edu')`), or more comfortably
it can be initialized at the module level with:

```py
import entrez as ez
ez.EMAIL = 'me@here.edu'
```

and from that point on, all the queries will have the email
automatically incorporated.

Similarly, an [API
key](https://ncbiinsights.ncbi.nlm.nih.gov/2017/11/02/new-api-keys-for-the-e-utilities/)
can be passed to any of the functions as an argument
(`equery(..., api_key='ABCD123')`), or initialized and incorporated
automatically from that moment with:

```py
import entrez as ez
ez.API_KEY = 'ABCD123'
```


## Tests

You can run the tests in the `tests` directory with:

```sh
pytest
```

which will run all the functions that start with `test_` in the
`test_*.py` files.


## References

* [Introduction to the E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25497/)
* [Retrieving large datasets](https://www.ncbi.nlm.nih.gov/books/NBK25498/#chapter3.Application_3_Retrieving_large)
* [Converting accession numbers](https://www.ncbi.nlm.nih.gov/books/NBK25498/#chapter3.Application_2_Converting_access)
* [API keys](https://ncbiinsights.ncbi.nlm.nih.gov/2017/11/02/new-api-keys-for-the-e-utilities/)


## Extra documentation

There is some more information in the [doc](doc) directory, and on the
[wiki](https://gitlab.com/jordibc/entrez/-/wikis/).


## License

This program is licensed under the GPL v3. See the [project
license](doc/license.md) for further details.


## Alternatives

When I initially wrote this module (circa 2016) there were no python
alternatives (that I could find). That also explains why I chose to
name it simply "entrez". Thanks to a more recent module,
[easy-entrez](https://pypi.org/project/easy-entrez/), here is a
collection of alternatives:

* [easy-entrez](https://pypi.org/project/easy-entrez/)
* [biopython.Entrez](https://biopython.org/docs/1.74/api/Bio.Entrez.html)
* [pubmedpy](https://github.com/dhimmel/pubmedpy)
* [entrezpy](https://gitlab.com/ncbipy/entrezpy)
