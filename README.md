# Entrez - Call the NCBI E-utilities from Python

A simple Python interface to **query the biological databases** kept at the NCBI.
It uses the Entrez Programming Utilities (*E-utilities*), nine server-side
programs that access the Entrez query and database system at the National Center
for Biotechnology Information (NCBI).

The interface is in the file ``entrez.py``. It contains two generators:

 * ``equery(tool[, ...])`` - Yield the response of a query with the given tool.
 * ``eselect(tool, db[, ...])`` - Return a dict that references the elements
    selected with tool over database db.
 * ``eapply(tool, db, elems[, retmax, ...])`` - Yield the response of applying
    a tool on db for the selected elements.
 * ``on_search(db, term, tool[, db2, ...])`` - Yield the response of applying a
    tool over the results of a search query.

There is a program ``sample_applications.py`` that shows how the [sample
applications of the E-utilities](http://www.ncbi.nlm.nih.gov/books/NBK25498)
would look like with this interface.

There is also a little program ``acc2gi.py`` that uses the library to
convert accession numbers into GIs.

### Examples of use

- Fetch information for SNP with id 3000, as in the example of
  http://www.ncbi.nlm.nih.gov/projects/SNP/SNPeutils.htm:

```python
for line in equery(tool='fetch', db='snp', id='3000'):
    print(line)
```

 * Get a summary of nucleotides related to accession numbers
   `NC_010611.1` and `EU477409.1`:

```python
for line in on_search(db='nucleotide',
                      term='NC_010611.1[accs] OR EU477409.1[accs]',
                      tool='summary'):
    print(line)
```

 * Download all chimpanzee mRNA sequences in FASTA format (our version
   of the [sample application
   3](http://www.ncbi.nlm.nih.gov/books/NBK25498/#chapter3.Application_3_Retrieving_large)):

```python
with open('chimp.fna', 'w') as fout:
    for line in on_search(db='nucleotide',
                          term='chimpanzee[orgn] AND biomol mrna[prop]',
                          tool='fetch', rettype='fasta'):
        fout.write(line + '\n')
```

### References

 * [Introduction to the E-utilities](http://www.ncbi.nlm.nih.gov/books/NBK25497/)
 * [Retrieving large datasets](http://www.ncbi.nlm.nih.gov/books/NBK25498/#chapter3.Application_3_Retrieving_large)
 * [Converting accession numbers](http://www.ncbi.nlm.nih.gov/books/NBK25498/#chapter3.Application_2_Converting_access)
