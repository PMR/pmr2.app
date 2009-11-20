from cStringIO import StringIO
import zope.interface
import zope.component
from zope.app.container.contained import Contained
from zope.annotation import factory
from zope.schema import fieldproperty
from zope.publisher.interfaces import IPublisherRequest
from persistent import Persistent
from Acquisition import aq_inner, aq_parent
from Products.CMFCore.utils import getToolByName

from pmr2.mercurial import Storage  # XXX remove later [1]
from pmr2.mercurial.interfaces import IPMR2StorageBase, IPMR2HgWorkspaceAdapter
from pmr2.mercurial.adapter import PMR2StorageAdapter
from pmr2.mercurial.adapter import PMR2StorageFixedRevAdapter
from pmr2.mercurial.adapter import PMR2StorageRequestAdapter
from pmr2.mercurial.exceptions import PathNotFoundError
from pmr2.mercurial import WebStorage

from pmr2.processor.cmeta import Cmeta
from pmr2.app.interfaces import *
from pmr2.app.browser.interfaces import IPublishTraverse
import pmr2.app.util


class PMR2StorageRequestViewAdapter(PMR2StorageRequestAdapter):
    """\
    This adapter is more suited from within views that implment
    IPublishTraverse within this product.

    If we customized IPublishTraverse and adapt it into the request
    (somehow) we could possibly do away with this adapter.  We could do
    refactoring later if we have a standard implementation of 
    IPublishTraverse that captures the request path.
    """

    def __init__(self, context, request, view):
        """
        context -
            The object to turn into a workspace
        request -
            The request
        view -
            The view that implements IPublishTraverse
        """

        assert IPublishTraverse.providedBy(view)
        # populate the request with values derived from view.
        if view.traverse_subpath:
            request['rev'] = view.traverse_subpath[0]
            request['request_subpath'] = view.traverse_subpath[1:]
        PMR2StorageRequestAdapter.__init__(self, context, request)


class PMR2ExposureStorageAdapter(PMR2StorageFixedRevAdapter):

    def __init__(self, context):

        self.context = context
        self.workspace = zope.component.queryMultiAdapter(
            (context,),
            name='ExposureToWorkspace',
        )
        self._rev = context.commit_id
        self._path = ()
        PMR2StorageFixedRevAdapter.__init__(self, self.workspace, self._rev)


class PMR2ExposureStorageURIResolver(PMR2ExposureStorageAdapter):

    def __init__(self, context):
        pass


class PMR2ExposureDocStorageAdapter(PMR2StorageFixedRevAdapter):
    """\
    """

    def __init__(self, context):

        self.context = context
        self.workspace = None
        ctx = aq_inner(context)
        while ctx is not None and self.workspace is None:
            obj = zope.component.queryMultiAdapter(
                (ctx,),
                name='ExposureToWorkspace',
            )
            if obj is not None:
                self.exposure = context
                self.workspace = obj
            ctx = aq_parent(ctx)

        self._rev = self.exposure.commit_id
        self._path = self.context.origin
        WebStorage.__init__(self, self.workspace.get_path(), self._rev)

    @property
    def rawfile(self):
        return self.file(self._path)


class PMR2StorageURIResolver(PMR2StorageAdapter):
    """\
    Storage class that supports resolution of URIs.
    """

    def path_to_uri(self, rev=None, filepath=None, view=None, validate=True):
        """
        Returns URI to a location within the workspace this exposure is
        derived from.

        Parameters:

        rev
            revision, commit id.  If None, and filepath is requested,
            it will default to the latest commit id.

        filepath
            The path fragment to the desired file.  Examples:

            - 'dir/file' - Link to the file
                e.g. http://.../workspace/name/@@view/rev/dir/file
            - '' - Link to the root of the manifest
                e.g. http://.../workspace/name/@@view/rev/
            - None - The workspace "homepage"

            Default: None

        view
            The view to use.  @@file for the file listing, @@rawfile for
            the raw file (download link).  See browser/configure.zcml 
            for a listing of views registered for this object.

            Default: None (@@rawfile)

        validate
            Whether to validate whether filepath exists.

            Default: True
        """

        frag = self.context.absolute_url(),

        if filepath is not None:
            # we only need to resolve the rest of the path here.
            if not view:
                # XXX magic?
                view = '@@rawfile'

            if not rev:
                self._changectx()
                rev = self.rev 

            if validate:
                try:
                    test = self.fileinfo(rev, filepath).next()
                except PathNotFoundError:
                    return None

            frag += (view, rev, filepath,)

        result = '/'.join(frag)
        return result


def ExposureToWorkspaceAdapter(context):
    """\
    Adapts an exposure object into workspace.
    """

    # XXX magic string, at least until we support user created workspace
    # root folders.
    workspace_folder = ('workspace',)

    catalog = getToolByName(context, 'portal_catalog')
    path = '/'.join(context.getPhysicalPath()[0:-2] + workspace_folder)

    # XXX path assumption.
    q = {
        'id': context.workspace,
        'path': {
            'query': path,
            'depth': len(workspace_folder),
        }
    }
    result = catalog(**q)
    if not result:
        # XXX manual gathering not implemented.
        raise WorkspaceObjNotFoundError()
    # there should be only one such id in the workspace for this
    # unique result.
    return result[0].getObject()


class ExposureSourceAdapter(object):
    """\
    See interface.
    """

    zope.interface.implements(IExposureSourceAdapter)

    def __init__(self, context):
        """
        context - any exposure object
        """

        self.context = context

    def source(self):
        # this could be nested in some folders, so we need to acquire
        # the parents up to the Exposure object.
        obj = aq_inner(self.context)
        paths = []
        while obj is not None:
            if IExposure.providedBy(obj):
                # as paths were appended...
                paths.reverse()
                workspace = zope.component.queryMultiAdapter(
                    (obj,),
                    name='ExposureToWorkspace',
                )
                return obj, workspace, '/'.join(paths)
            paths.append(obj.getId())
            obj = aq_parent(obj)
        # XXX could benefit from a better exception type?
        raise ValueError('cannot acquire Exposure object')

    def file(self):
        """\
        Returns contents of this file.
        """

        # While a view could technically be defined to return this, it 
        # is better to generate the redirect to the actual file in the
        # workspace.

        exposure, workspace, path = self.source()
        storage = zope.component.queryMultiAdapter(
            (workspace, exposure.commit_id,),
            name='PMR2StorageFixedRev',
        )
        return storage.file(path)


class ExposureFileNoteSourceAdapter(ExposureSourceAdapter):

    def __init__(self, context):
        self.context = context.__parent__
        # Since an annotation note should have a parent that provides
        # IExposureObject, this should pass
        assert IExposureObject.providedBy(self.context)


class ExposureDocViewGenSourceAdapter(ExposureSourceAdapter):

    zope.interface.implements(IExposureDocViewGenSourceAdapter)

    def source(self):
        exposure, workspace, path = ExposureSourceAdapter.source(self)
        # Since this is for document source, Exposure objects has
        # special handling procedures.
        if IExposure.providedBy(self.context):
            # as the root Exposure object can specify a path for now we
            # lock it to a specific field for now
            path = self.context.docview_gensource
        return exposure, workspace, path


# Basic support for ExposureFileNote annotation adapters.

class ExposureFileNoteBase(Persistent, Contained):
    """\
    The base class for adapter to ExposureFile objects.  Both parent
    classes are required.
    """

    zope.component.adapts(IExposureFile)
    zope.interface.implements(IExposureFileNote)


class ExposureFileEditableNoteBase(ExposureFileNoteBase):
    """\
    Base class for editable notes.
    """

    zope.interface.implements(IExposureFileEditableNote)


class StandardExposureFile(ExposureFileNoteBase):
    """\
    A dummy of sort that will just reuse the ExposureFile that this
    adapts.
    """

    zope.interface.implements(IStandardExposureFile)

StandardExposureFileFactory = factory(StandardExposureFile)


class RawTextNote(ExposureFileNoteBase):
    """\
    See IRawText interface.
    """

    zope.interface.implements(IRawTextNote)
    text = fieldproperty.FieldProperty(IRawTextNote['text'])

    def raw_text(self):
        return self.text


class GroupedNote(ExposureFileNoteBase):
    """\
    See IGroupedNote interface.
    """

    zope.interface.implements(IGroupedNote)
    active_notes = fieldproperty.FieldProperty(IGroupedNote['active_notes']) 

BasicMathMLNoteFactory = factory(RawTextNote, 'basic_mathml')
BasicCCodeNoteFactory = factory(RawTextNote, 'basic_ccode')


class CmetaNote(ExposureFileNoteBase):
    """\
    Contains a rendering of the CellML Metadata.
    """
    # XXX this class should be part of the metadata, and registered into
    # some sort of database that will automatically load this up into
    # one of the valid document types that can be added.

    zope.interface.implements(ICmetaNote)

    metadata = fieldproperty.FieldProperty(ICmetaNote['metadata'])

    model_title = fieldproperty.FieldProperty(ICmetaNote['model_title'])
    model_author = fieldproperty.FieldProperty(ICmetaNote['model_author'])
    model_author_org = fieldproperty.FieldProperty(ICmetaNote['model_author_org'])

    citation_authors = fieldproperty.FieldProperty(ICmetaNote['citation_authors'])
    citation_title = fieldproperty.FieldProperty(ICmetaNote['citation_title'])
    citation_bibliographicCitation = fieldproperty.FieldProperty(ICmetaNote['citation_bibliographicCitation'])
    citation_id = fieldproperty.FieldProperty(ICmetaNote['citation_id'])
    citation_issued = fieldproperty.FieldProperty(ICmetaNote['citation_issued'])
    keywords = fieldproperty.FieldProperty(ICmetaNote['keywords'])

    def citation_authors_string(self):
        if not self.citation_authors:
            return u''
        middle = u'</li>\n<li>'.join(
            ['%s, %s %s' % i for i in self.citation_authors])
        return u'<ul>\n<li>%s</li>\n</ul>' % middle

    def citation_id_html(self):
        if not self.citation_id:
            return u''
        http = pmr2.app.util.uri2http(self.citation_id)
        if http:
            return '<a href="%s">%s</a>' % (http, self.citation_id)
        return self.citation_id

    def get_authors_family_index(self):
        if self.citation_authors:
            return [pmr2.app.util.normal_kw(i[0]) 
                    for i in self.citation_authors]
        else:
            return []

    def get_citation_title_index(self):
        if self.citation_title:
            return pmr2.app.util.normal_kw(self.citation_title)

    def get_keywords_index(self):
        if self.keywords:
            results = [pmr2.app.util.normal_kw(i[1]) for i in self.keywords]
            results.sort()
            return results
        else:
            return []

    def keywords_string(self):
        return ', '.join(self.get_keywords_index())

    def pmr1_citation_authors(self):
        if self.citation_authors and self.citation_issued:
            authors = u', '.join([i[0] for i in self.citation_authors])
            return u'%s, %s' % (authors, self.citation_issued[:4])
        else:
            return u''

    def pmr1_citation_title(self):
        if self.citation_title:
            return self.citation_title
        else:
            return u''

CmetaNoteFactory = factory(CmetaNote, 'cmeta')
