# Entrez - Call the NCBI E-utilities from Python

A simple Python interface to **query the biological databases** kept at the NCBI.
It uses the Entrez Programming Utilities (*E-utilities*), nine server-side
programs that access the Entrez query and database system at the National Center
for Biotechnology Information (NCBI).

The interface is in the file ``entrez.py``. It contains:

 * ``equery(tool[, ...])`` - Yield the response of a query with the given tool.
 * ``eselect(tool, db[, ...])`` - Return a dict that references the elements
    selected with tool over database db.
 * ``eapply(tool, db, elems[, retmax, ...])`` - Yield the response of applying
    a tool on db for the selected elements.
 * ``on_search(db, term, tool[, db2, ...])`` - Yield the response of applying a
    tool over the results of a search query.

The most useful function is `equery`. The function `eselect` makes a selection
of elements on the server, that can be referenced later for future queries
(instead of downloading a long list of ids that then we would have to send to
the server again). The function `eapply` can run a tool like `equery`, but using
a previous selection of elements (made with `eselect`). Finally, `on_search` is
a convenience function that combines the results of a `eselect` on an `eapply`,
which is a very common case.

There is a program ``sample_applications.py`` that shows how the [sample
applications of the E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25498)
would look like with this interface.

There are also some little programs: ``acc2gi.py`` uses the library to
convert accession numbers into GIs, and ``sra2runacc.py`` uses entrez to get all the run accession numbers for a given SRA study.

### Examples of use

- Fetch information for SNP with id 3000, as in the example at
  https://www.ncbi.nlm.nih.gov/projects/SNP/SNPeutils.htm:

```python
for line in equery(tool='fetch', db='snp', id='3000'):
    print(line)
```

 * Get a summary of nucleotides related to accession numbers
   `NC_010611.1` and `EU477409.1`:

```python
for line in on_search(db='nucleotide',
                      term='NC_010611.1[accn] OR EU477409.1[accn]',
                      tool='summary'):
    print(line)
```

 * Download all chimpanzee mRNA sequences in FASTA format (our version
   of the [sample application
   3](https://www.ncbi.nlm.nih.gov/books/NBK25498/#chapter3.Application_3_Retrieving_large)):

```python
with open('chimp.fna', 'w') as fout:
    for line in on_search(db='nucleotide',
                          term='chimpanzee[orgn] AND biomol mrna[prop]',
                          tool='fetch', rettype='fasta'):
        fout.write(line + '\n')
```

### API keys

An [API key](https://ncbiinsights.ncbi.nlm.nih.gov/2017/11/02/new-api-keys-for-the-e-utilities/)
can be passed to any of the functions as an argument (for example,
`equery(..., api_key='ABCD123')`), or it can be initialized at the module level
with:

```python
import entrez
entrez.API_KEY = 'ABCD123'
```

and from that point on, all the queries will have the API key automatically
incorporated.


### References

 * [Introduction to the E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25497/)
 * [Retrieving large datasets](https://www.ncbi.nlm.nih.gov/books/NBK25498/#chapter3.Application_3_Retrieving_large)
 * [Converting accession numbers](https://www.ncbi.nlm.nih.gov/books/NBK25498/#chapter3.Application_2_Converting_access)
 * [API keys](https://ncbiinsights.ncbi.nlm.nih.gov/2017/11/02/new-api-keys-for-the-e-utilities/)
