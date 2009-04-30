import zope.schema
import zope.interface

from zope.i18nmessageid import MessageFactory
_ = MessageFactory("pmr2")

from pmr2.app.schema import ObjectId, WorkspaceList, CurationDict


class ObjectIdExistsError(zope.schema.ValidationError):
    __doc__ = _("""The specified id is already in use.""")


class InvalidPathError(zope.schema.ValidationError):
    __doc__ = _("""The value specified is not a valid path.""")


class RepoRootNotExistsError(zope.schema.ValidationError):
    __doc__ = _("""The repository root at the specified path does not exist.""")


class RepoNotExistsError(zope.schema.ValidationError):
    __doc__ = _("""The repository at the specified path does not exist.""")


class RepoPathUndefinedError(zope.schema.ValidationError):
    __doc__ = _("""The repository path is undefined.""")


class WorkspaceDirNotExistsError(zope.schema.ValidationError):
    __doc__ = _("""The workspace directory does not exist.""")


class WorkspaceObjNotFoundError(zope.schema.ValidationError):
    __doc__ = _("""The workspace object is not found.""")


class IObjectIdMixin(zope.interface.Interface):
    """\
    For use by any interface that will be used by AddForm; this
    basically gives an 'id' field for the user to input.
    """

    id = ObjectId(
        title=u'Id',
        description=u'The identifier of the object, used for URI.',
    )


class IPMR2(zope.interface.Interface):
    """\
    Interface for the root container for the entire model repository.
    """

    title = zope.schema.TextLine(
        title=u'Title',
        description=u'The title or name given to this repository.',
    )

    repo_root = zope.schema.BytesLine(
        title=u'Repository Path',
        description=u'The working directory of this repository. This '
                     'directory contains the raw VCS repositories of the '
                     'models.',
        readonly=False,
    )

    # workspace_path is 'workspace'
    # sandbox_path is 'sandbox'


class IPMR2Add(IObjectIdMixin, IPMR2):
    """\
    Interface for the use by PMR2AddForm.
    """


class IWorkspaceContainer(zope.interface.Interface):
    """\
    Container for the model workspaces.
    """

    title = zope.schema.TextLine(
        title=u'Title',
        default=u'Workspace',
    )

    get_repository_list, = zope.schema.accessors(WorkspaceList(
        title=u'Repository List',
        readonly=True,
    ))

    def get_path():
        """\
        Returns the root directory where all the workspaces are stored.
        """


class ISandboxContainer(zope.interface.Interface):
    """\
    Container for the sandboxes (working copies).
    """

    title = zope.schema.TextLine(
        title=u'Title',
        default=u'Sandbox',
    )

    def get_path():
        """\
        Returns the root directory where all the sandboxes are stored.
        """


class IExposureContainer(zope.interface.Interface):
    """\
    Container for all exposure pages.
    """

    title = zope.schema.TextLine(
        title=u'Title',
        default=u'Exposure',
    )


class IWorkspace(zope.interface.Interface):
    """\
    Model workspace.
    """

    # id would be the actual path on filesystem

    title = zope.schema.TextLine(
        title=u'Title',
        required=False,
    )

    description = zope.schema.Text(
        title=u'Description',
        required=False,
    )

    def get_path():
        """\
        Returns path on the filesystem to this instance of workspace.
        """


class IWorkspaceAdd(IObjectIdMixin, IWorkspace):
    """\
    Interface for the use by WorkspaceAddForm.
    """


class IWorkspaceBulkAdd(zope.interface.Interface):
    """\
    Interface for the use by WorkspaceAddForm.
    """

    workspace_list = zope.schema.Text(
        title=u'List of Workspaces',
        description=u'List of Mercurial Repositories created by pmr2_mkhg ' \
                     'that are already moved into the workspace directory.',
        required=True,
    )


class ISandbox(zope.interface.Interface):
    """\
    Container for the sandboxes (working copies).
    """

    title = zope.schema.TextLine(
        title=u'Title',
    )

    description = zope.schema.Text(
        title=u'Description',
    )

    status = zope.schema.Text(
        title=u'Status Messages',
        description=u'Status output from VCS',
    )

    def get_path():
        """\
        Returns path on the filesystem to this instance of sandbox.
        """


class IExposure(zope.interface.Interface):
    """\
    Container for all exposure pages.
    """

    title = zope.schema.TextLine(
        title=u'Title',
    )

    workspace = zope.schema.TextLine(
        title=u'Workspace',
        description=u'The model workspace this exposure encapsulates.',
    )

    commit_id = zope.schema.TextLine(
        title=u'Commit ID',
        description=u'The specific commit identifier of the model.',
    )

    curation = CurationDict(
        title=u'Curation',
        description=u'Curation of this model.',
        required=False,
    )

    def get_path():
        """\
        Returns path on the filesystem to this instance of workspace.
        """


class IExposureDocGen(zope.interface.Interface):
    """\
    Interface for the documentation generation.
    """

    filename = zope.schema.Choice(
        title=u'Documentation File',
        description=u'The file where the documentation resides in.',
        vocabulary='ManifestListVocab',
    )

    exposure_factory = zope.schema.Choice(
        title=u'Exposure Type',
        description=u'The method to convert the file selected into HTML for use by exposure.',
        vocabulary='ExposureDocumentFactoryVocab',
        required=False,
    )


class IExposureMetadocGen(zope.interface.Interface):
    """\
    Interface for the generation of metadocumentation.
    """

    filename = zope.schema.Choice(
        title=u'Documentation File',
        description=u'The file to generate the set of exposures with.',
        vocabulary='ManifestListVocab',
    )

    exposure_factory = zope.schema.Choice(
        title=u'Exposure Type',
        description=u'The type of exposure to generate.',
        vocabulary='ExposureMetadocFactoryVocab',
        required=False,
    )


class IBaseExposureDocument(zope.interface.Interface):
    """\
    Base interface for all types of exposure documents.
    """

    def generate_content():
        """\
        The method to generate/populate content for an exposure document.
        """


class IExposureDocument(IBaseExposureDocument):
    """\
    Interface for an exposure document.
    """

    origin = zope.schema.TextLine(
        title=u'Origin File',
        description=u'Name of the file that this document was generated from.',
        required=False,
    )

    transform = zope.schema.TextLine(
        title=u'Transform',
        description=u'Name of the transform that this was generated from.',
        required=False,
    )

    metadoc = zope.schema.TextLine(
        title=u'Metadoc',
        description=u'The meta-documentation page that this exposure subpage is part of.',
        required=False,
    )


class IExposureMetadoc(IBaseExposureDocument):
    """\
    Interface for an exposure document that creates a set of exposure
    documents.
    """

    origin = zope.schema.Text(
        title=u'Origin Files',
        description=u'Name of the file that this document was generated from.',
    )

    factories = zope.schema.List(
        title=u'Factories',
        description=u'The list of factories that was used to generate this meta-documentation from origin.',
    )

    subdocuments = zope.schema.List(
        title=u'Sub documents',
        description=u'The sub-documents that were created during document generation.',
    )


class IExposureMathDocument(IExposureDocument):
    """\
    Exposure Document with embedded MathML.
    """

    mathml = zope.schema.Text(
        title=u'MathML',
        description=u'The MathML content',
    )


class IExposureCodeDocument(IExposureDocument):
    """\
    Exposure Document for code.
    """

    raw_code = zope.schema.Text(
        title=u'Raw Code',
        description=u'The raw code',
    )


class IExposureCmetaDocument(IExposureDocument):
    """\
    Exposure Document that handles CellML Metadata.
    """

    metadata = zope.schema.Text(
        title=u'Metadata',
        description=u'The metadata content',
    )

    citation_authors = zope.schema.List(
        title=u'Citation Authors',
        description=u'List of authors of this citation',
    )

    citation_title = zope.schema.TextLine(
        title=u'Citation Title',
        description=u'The title of this citation (e.g. the title of a journal article)',
    )

    citation_bibliographicCitation = zope.schema.TextLine(
        title=u'Bibliographic Citation',
        description=u'The source of the article',
    )

    citation_id = zope.schema.TextLine(
        title=u'Citation Id',
        description=u'The unique identifier for this citation (such as Pubmed).',
    )

    keywords = zope.schema.List(
        title=u'Keywords',
        description=u'The keywords of this model.',
    )


class IExposurePMR1Metadoc(IExposureMetadoc):
    """\
    Interface for the PMR1 set of exposure documents.
    """


class IBaseExposureDocumentFactory(zope.interface.Interface):
    """\
    Base interface for exposure document types factory.
    """

    klass = zope.schema.TextLine(
        title=u'Name of the ExposureDocument class.',
    )

    description = zope.schema.Text(
        title=u'Description.',
    )

    suffix = zope.schema.TextLine(
        title=u'Default suffix',
    )


class IExposureDocumentFactory(IBaseExposureDocumentFactory):
    """
    For factories that creates exposure documents.
    """

    transform = zope.schema.TextLine(
        title=u'Transform to use',
        required=False,
    )


class IExposureMetadocFactory(IBaseExposureDocumentFactory):
    """
    Interface for meta-document factories.
    """

    factories = zope.schema.List(
        title=u'Factories',
        description=u'The list of factories that will be used to generate this meta-documentation for the origin files.',
    )


class IPMR2Search(zope.interface.Interface):
    """\
    Interface for the search objects.
    """

    title = zope.schema.TextLine(
        title=u'Title',
    )

    description = zope.schema.Text(
        title=u'Description',
        required=False,
    )

    catalog_index = zope.schema.Choice(
        title=u'Index',
        description=u'The index to be use by this search object.',
        vocabulary='PMR2IndexesVocab',
    )


class IPMR2SearchAdd(IObjectIdMixin, IPMR2Search):
    """\
    Interface for the use by PMR2AddForm.
    """


class IExposureContentIndex(zope.interface.Interface):
    """\
    Interface for methods that will return a workable index.  All 
    exposure objects need to implement this to make catalog contain data
    that will make sense for presentation.

    Basically acquisition of parent methods by child will cause the
    child to be indexed, causing pollution of index and complication in 
    querying.

    Ideally this interface should not have to exist, if the catalog/
    indexing tools are more flexible in allowing what kind of data to 
    include for an object.  Implementation of this class is only a 
    demonstration of what I intend to do, which is to have subobjects
    hold into the keys they hold onto, but the URI will be taken to the
    parent object, and subobjects do not have keys to the parent object.

    Yes, this interface and implementation is a giant workaround of the
    flaws in ZCatalog and how Plone use them.  Unfortunately at this
    stage it is faster to workaround their issues than to roll our own
    cataloging solution based on zope.app.catalog (or RDF store, which
    is in the future).
    """

    def get_authors_family_index():
        pass

    def get_citation_title_index():
        pass

    def get_curation_index():
        pass

    def get_keywords_index():
        pass

    def get_exposure_workspace_index():
        pass
