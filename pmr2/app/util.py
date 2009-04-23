from lxml import etree

import pmr2.mercurial.utils

CELLML_NSMAP = {
    'tmpdoc': 'http://cellml.org/tmp-documentation',
    'pcenv': 'http://www.cellml.org/tools/pcenv/',
    'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
}

def set_xmlbase(xml, base):
    try:
        dom = etree.fromstring(xml)
    except:
        # silently aborting on invalid input.
        return xml
    dom.set('{http://www.w3.org/XML/1998/namespace}base', base)
    result = etree.tostring(dom, encoding='utf-8', xml_declaration=True)
    return result

def fix_pcenv_externalurl(xml, base):
    """
    A workaround for PCEnv session specification bug
    https://tracker.physiomeproject.org/show_bug.cgi?id=1079

    Briefly, pcenv:externalurl is really a URI reference, but it is
    represented as a literal string, hence it does not benefit from
    the declaration of xml:base.

    this manually replaces externalurl with the xml:base fragment 
    inserted in front of it.
    """

    try:
        dom = etree.fromstring(xml)
    except:
        # silently aborting on invalid input.
        return xml

    externalurl = '{http://www.cellml.org/tools/pcenv/}externalurl'

    # RDF representation generated by PCEnv
    xulnodes = dom.xpath('.//rdf:Description[@pcenv:externalurl]',
        namespaces=CELLML_NSMAP)
    for node in xulnodes:
        xulname = node.xpath('string(@pcenv:externalurl)', 
            namespaces=CELLML_NSMAP)
        if xulname:
            node.attrib[externalurl] = '/'.join([base, xulname])

    # Different form of RDF presentation
    xulnodes = dom.xpath('.//pcenv:externalurl',
        namespaces=CELLML_NSMAP)
    for node in xulnodes:
        xulname = node.text
        if xulname:
            node.text = '/'.join([base, xulname])

    result = etree.tostring(dom, encoding='utf-8', xml_declaration=True)
    return result

infouri_prefix = {
    'info:pmid': 'http://www.ncbi.nlm.nih.gov/pubmed',
    'urn:miriam:pubmed': 'http://www.ncbi.nlm.nih.gov/pubmed',
}

def infouri2http(infouri):
    """\
    Resolves an info-uri into an http link based on the lookup table 
    above.
    """

    fragments = infouri.split('/', 1)
    if fragments[0] in infouri_prefix:
        return '/'.join([infouri_prefix[fragments[0]], fragments[1]])
    return None

def obfuscate(input):
    try:
        text = input.decode('utf8')
    except UnicodeDecodeError:
        text = input
    return ''.join(['&#%d;' % ord(c) for c in text])

def short(input):
    return pmr2.mercurial.utils.filter(input, 'short')

