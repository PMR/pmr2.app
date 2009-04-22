import os.path

from zope import interface
from zope.schema import fieldproperty

from Acquisition import aq_parent, aq_inner

from Products.CMFDynamicViewFTI.browserdefault import BrowserDefaultMixin
from Products.ATContentTypes.content.folder import ATFolder, ATBTreeFolder
from Products.ATContentTypes.content.document import ATDocument
from Products.Archetypes import atapi

import pmr2.mercurial
import pmr2.mercurial.utils

from pmr2.app.interfaces import *
from pmr2.app.mixin import TraversalCatchAll


class WorkspaceContainer(ATBTreeFolder):
    """\
    Container for workspaces in PMR2.
    """

    interface.implements(IWorkspaceContainer)

    # title is defined by ATFolder

    def __init__(self, oid='workspace', **kwargs):
        super(WorkspaceContainer, self).__init__(oid, **kwargs)

    def get_path(self):
        """See IWorkspaceContainer"""

        p = aq_parent(aq_inner(self)).repo_root
        if not p:
            return None
        # XXX magic string
        return os.path.join(p, 'workspace')

    def get_repository_list(self):
        """\
        Implementation of the accessor from IWorkspaceContainer
        
        Returns a list of tuples.  Format is:
        - name of directory
        - whether the object associated with is valid.

          - True means yes
          - None means missing
          - False means object should not exist.  It is either the wrong
            type, or the repository directory is missing on the file
            system.
        """

        reporoot = self.get_path()
        if not reporoot:
            raise RepoPathUndefinedError('repo path is undefined')

        try:
            repodirs = pmr2.mercurial.utils.webdir(reporoot)
        except OSError:
            raise WorkspaceDirNotExistsError()

        # code below is slightly naive, performance-wise.  if done in
        # same loop, popping both list as a stack, compare the values
        # that are popped might be faster.

        # objects need to be processed
        # True = correct type (Workspace), False = incorrect type
        items = self.items()
        repoobjs = [
            (i[0], isinstance(i[1], Workspace),)
            for i in items]
        repoobjs_d = dict(repoobjs)

        # check to see if a repo dir has object of same name
        # None = missing, True/False (from above if exists)
        check = [(i, repoobjs_d.get(i, None)) for i in repodirs]

        # failure due to non-existing objects (remaining repoobjs that
        # were not checked
        # False = repo missing/invalid Workspace object
        fail = [(i[0], False) for i in repoobjs if i[0] not in repodirs]

        # build the result and sort
        result = fail + check
        result.sort()

        return result

atapi.registerType(WorkspaceContainer, 'pmr2.app')


class Workspace(BrowserDefaultMixin, atapi.BaseContent):
    """\
    PMR2 Workspace object is used to connect to the repository of model
    and related data.
    """

    interface.implements(IWorkspace)

    description = fieldproperty.FieldProperty(IWorkspace['description'])

    def get_path(self):
        """See IWorkspace"""

        # aq_inner needed to get out of form wrappers
        p = aq_parent(aq_inner(self)).get_path()
        if not p:
            return None
        return os.path.join(p, self.id)

    def get_log(self, rev=None, branch=None, shortlog=False, datefmt=None, 
                maxchanges=None):
        """See IWorkspace"""

        # XXX valid datefmt values might need to be documented/checked
        storage = self.get_storage()
        return storage.log(rev, branch, shortlog, datefmt, maxchanges).next()

    def get_storage(self):
        """See IWorkspace"""

        path = self.get_path()
        return pmr2.mercurial.Storage(path)

    def get_workspace_container(self):
        """\
        returns the workspace container object that stores this.
        """

        # FIXME get rid of this assumption
        result = aq_parent(aq_inner(self))
        return result

    def get_pmr2_container(self):
        """\
        returns the root pmr2 object that stores this.
        """

        # FIXME get rid of this assumption
        result = aq_parent(self.get_workspace_container())
        return result

atapi.registerType(Workspace, 'pmr2.app')