A simple Python interface to the amazing NCBI databases (Entrez).

The interface is in file `entrez.py`. It contains::

- `equery(tool, ...)` - Return the http response of a query.
- `eapply(db, term, tool[, db2, retmax, ...])` - Yield the output of
  applying a tool over the results of a query.

There is also a little program `acc2gi.py` that uses the library to
convert accession numbers into GIs.

Examples of use:

- Fetch information for SNP with id 3000, as in the example of
  http://www.ncbi.nlm.nih.gov/projects/SNP/SNPeutils.htm::

      for line in equery(tool='fetch', db='snp', id='3000'):
          print(line.rstrip())

- Get a summary of nucleotides related to accession numbers
  NC_010611.1 and EU477409.1::

      for line in eapply(db='nucleotide',
                         term='NC_010611.1[accs] OR EU477409.1[accs]',
                         tool='summary'):
          print(line.rstrip())

References:

- E-Utilities: http://www.ncbi.nlm.nih.gov/books/NBK25497/#chapter2.The_Nine_Eutilities_in_Brief
- Retrieving large datasets: http://www.ncbi.nlm.nih.gov/books/NBK25498/#chapter3.Application_3_Retrieving_large
- Converting accession numbers: http://www.ncbi.nlm.nih.gov/books/NBK25498/#chapter3.Application_2_Converting_access


[![Join the chat at https://gitter.im/jordibc/entrez](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/jordibc/entrez?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)