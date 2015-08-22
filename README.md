# Entrez - Call the NCBI E-utilities from Python

A simple Python interface to **query the biological databases** kept at the NCBI.
It uses the Entrez Programming Utilities (*E-utilities*), nine server-side
programs that access the Entrez query and database system at the National Center
for Biotechnology Information (NCBI).

The interface is in the file ``entrez.py``. It contains two generators:

 * ``equery(tool[, ...])`` - Yield the response of a query with the given tool.
 * ``eapply(db, term, tool[, db2, retmax, ...])`` - Yield the output of
   applying a tool over the results of a query.

There is also a little program ``acc2gi.py`` that uses the library to
convert accession numbers into GIs.

### Examples of use:

- Fetch information for SNP with id 3000, as in the example of
  http://www.ncbi.nlm.nih.gov/projects/SNP/SNPeutils.htm:

```python
for line in equery(tool='fetch', db='snp', id='3000'):
    print(line)
```

 * Get a summary of nucleotides related to accession numbers
   `NC_010611.1` and `EU477409.1`:

```python
for line in eapply(db='nucleotide',
                   term='NC_010611.1[accs] OR EU477409.1[accs]',
                   tool='summary'):
    print(line)
```

### References:

 * [Introduction to the E-utilities](http://www.ncbi.nlm.nih.gov/books/NBK25497/)
 * [Retrieving large datasets](http://www.ncbi.nlm.nih.gov/books/NBK25498/#chapter3.Application_3_Retrieving_large)
 * [Converting accession numbers](http://www.ncbi.nlm.nih.gov/books/NBK25498/#chapter3.Application_2_Converting_access)
