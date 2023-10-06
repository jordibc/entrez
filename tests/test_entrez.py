import sys

sys.path += ['.', '..']
import entrez as ez


def test_fetch():
    xml = ''.join(ez.equery(tool='fetch', db='snp', id='3000'))

    summary = ez.read_xml(xml)['DocumentSummary']

    assert summary['GENES'] == {'GENE_E': {'NAME': 'REST', 'GENE_ID': '5978'}}

    assert [x['MAF'] for x in summary['GLOBAL_MAFS']] == [
        {'STUDY': '1000Genomes', 'FREQ': 'T=0.308713/1546'},
        {'STUDY': 'ALSPAC', 'FREQ': 'T=0.377789/1456'},
        {'STUDY': 'Chileans', 'FREQ': 'T=0.442492/277'},
        {'STUDY': 'Estonian', 'FREQ': 'T=0.390179/1748'},
        {'STUDY': 'GENOME_DK', 'FREQ': 'T=0.35/14'},
        {'STUDY': 'GnomAD', 'FREQ': 'T=0.361096/50552'},
        {'STUDY': 'GoNL', 'FREQ': 'T=0.410822/410'},
        {'STUDY': 'HapMap', 'FREQ': 'T=0.267442/506'},
        {'STUDY': 'KOREAN', 'FREQ': 'T=0.241297/707'},
        {'STUDY': 'Korea1K', 'FREQ': 'T=0.25/458'},
        {'STUDY': 'NorthernSweden', 'FREQ': 'T=0.388333/233'},
        {'STUDY': 'Qatari', 'FREQ': 'T=0.449074/97'},
        {'STUDY': 'SGDP_PRJ', 'FREQ': 'C=0.402878/112'},
        {'STUDY': 'Siberian', 'FREQ': 'C=0.35/14'},
        {'STUDY': 'TOMMO', 'FREQ': 'T=0.221849/3718'},
        {'STUDY': 'TOPMED', 'FREQ': 'T=0.364317/96431'},
        {'STUDY': 'TWINSUK', 'FREQ': 'T=0.401564/1489'},
        {'STUDY': 'Vietnamese', 'FREQ': 'T=0.179245/38'},
        {'STUDY': 'ALFA', 'FREQ': 'T=0.386408/23601'}]


def test_on_search():
    xml = ''.join(ez.on_search(tool='summary', db='nucleotide',
                               term='NC_010611.1[accn] OR EU477409.1[accn]'))

    results = ez.read_xml(xml)['eSummaryResult']

    assert len(results) == 2

    assert [x['Item'] for x in results[0]['DocSum']['Item-group']] == [
        {'@Name': 'Caption', '@Type': 'String', 'text': 'NC_010611'},
        {'@Name': 'Title', '@Type': 'String',
         'text': 'Acinetobacter baumannii ACICU, complete sequence'},
        {'@Name': 'Extra', '@Type': 'String',
         'text': 'gi|184156320|ref|NC_010611.1|[184156320]'},
        {'@Name': 'Gi', '@Type': 'Integer', 'text': '184156320'},
        {'@Name': 'CreateDate', '@Type': 'String', 'text': '2008/04/21'},
        {'@Name': 'UpdateDate', '@Type': 'String', 'text': '2022/11/04'},
        {'@Name': 'Flags', '@Type': 'Integer', 'text': '800'},
        {'@Name': 'TaxId', '@Type': 'Integer', 'text': '405416'},
        {'@Name': 'Length', '@Type': 'Integer', 'text': '3904116'},
        {'@Name': 'Status', '@Type': 'String', 'text': 'live'},
        {'@Name': 'ReplacedBy', '@Type': 'String', 'text': ''},
        {'@Name': 'Comment', '@Type': 'String', 'text': '  '},
        {'@Name': 'AccessionVersion', '@Type': 'String', 'text': 'NC_010611.1'}]
