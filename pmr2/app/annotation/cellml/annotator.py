from cStringIO import StringIO

import zope.interface
import zope.component

from pmr2.processor.cmeta import Cmeta

import pmr2.app.util
from pmr2.app.factory import named_factory
from pmr2.app.annotation.interfaces import *
from pmr2.app.annotation.annotator import ExposureFileAnnotatorBase
from pmr2.app.annotation.annotator import ExposureFileEditableAnnotatorBase
from pmr2.app.annotation.annotator import PortalTransformAnnotatorBase


class CellML2MathMLAnnotator(PortalTransformAnnotatorBase):
    zope.interface.implements(IExposureFileAnnotator)
    transform = 'pmr2_processor_legacy_cellml2html_mathml'
    title = u'Basic MathML'
    label = u'Mathematics'
    description = u''

    def generate(self):
        return (
            ('text', self.convert(self.input).decode('utf8')),
        )

CellML2MathMLAnnotatorFactory = named_factory(CellML2MathMLAnnotator)


class CellML2CAnnotator(PortalTransformAnnotatorBase):
    zope.interface.implements(IExposureFileAnnotator)
    transform = 'pmr2_processor_cellmlapi_cellml2c'
    title = u'CellML C Code Generation'
    label = u'Procedural C Code'
    description = u''

    def generate(self):
        return (
            ('text', self.convert(self.input).decode('utf8')),
        )

CellML2CAnnotatorFactory = named_factory(CellML2CAnnotator)


class OpenCellSessionAnnotator(ExposureFileEditableAnnotatorBase):
    zope.interface.implements(IExposureFileAnnotator)
    title = u'OpenCell Session Link'
    label = u'OpenCell Session'

    def generate(self):
        return ()

OpenCellSessionAnnotatorFactory = named_factory(OpenCellSessionAnnotator)


class CmetaAnnotator(ExposureFileAnnotatorBase):
    zope.interface.implements(IExposureFileAnnotator)
    title = u'Basic CellML Metadata'
    label = u'Model Metadata'

    def generate(self):
        input = self.input
        result = {}
        metadata = Cmeta(StringIO(input))
        ids = metadata.get_cmetaid()
        if not ids:
            # got no metadata.
            return ()

        citation = metadata.get_citation(ids[0])
        if not citation:
            # no citation, everyone go home
            return ()

        result['citation_id'] = citation[0]['citation_id']
        # more than just journal
        result['citation_bibliographicCitation'] = citation[0]['journal']
        result['citation_title'] = citation[0]['title']

        # XXX ad-hoc sanity checking
        issued = citation[0]['issued']
        if pmr2.app.util.simple_valid_date(issued):
            result['citation_issued'] = issued
        else:
            result['citation_issued'] = u''

        authors = []
        for c in citation[0]['creator']:
            family = c['family']
            given = c['given']
            if c['other']:
                other = ' '.join(c['other'])
            else:
                other = ''
            fn = (family, given, other)
            authors.append(fn)
            
        result['citation_authors'] = authors
        result['keywords'] = metadata.get_keywords()

        dcvc = metadata.get_dc_vcard_info(node='')
        if dcvc:
            # using only first one
            info = dcvc[0]
            result['model_title'] = info['title']
            result['model_author'] = '%s %s' % (info['given'], info['family'])
            result['model_author_org'] = \
                '%s, %s' % (info['orgunit'], info['orgname']) 
        # annotators are expected to return a list of tuples.
        return result.items()

CmetaAnnotatorFactory = named_factory(CmetaAnnotator)
