import zope.component

from DateTime import DateTime

from pmr2.app.settings.interfaces import IPMR2GlobalSettings

def create_user_workspace(user, event):
    """\
    Create a user workspace upon user logging in.  Create the dummies.

        >>> import zope.interface
        >>> import zope.component
        >>>
        >>> class User(object):
        ...     def __init__(self, name):
        ...         self.name = name
        ...     def getName(self):
        ...         return self.name
        ...
        >>> class WorkspaceContainer(object):
        ...     def __init__(self, id):
        ...         self.id = id
        ...
        >>> class Settings(object):
        ...     zope.interface.implements(IPMR2GlobalSettings)
        ...     create_user_workspace = True
        ...     workspace = {}
        ...     def createUserWorkspaceContainer(self, name=None):
        ...         self.workspace[name] = WorkspaceContainer(name)
        ...
        >>> settings = Settings()
        >>> zope.component.getSiteManager().registerUtility(settings,
        ...     IPMR2GlobalSettings)
        >>> name = 'tester'
        >>> user = User(name)
        >>> # test
        >>> create_user_workspace(user, None)
        >>> settings.workspace[name].id
        'tester'
        >>> # cleanup
        >>> zope.component.getSiteManager().unregisterUtility(settings,
        ...     IPMR2GlobalSettings)
        True
    """

    settings = zope.component.queryUtility(IPMR2GlobalSettings)
    name = user.getName()
    settings.createUserWorkspaceContainer(name)

def set_pushed_workspace_datetime(workspace, event):
    workspace.setModificationDate(DateTime())

def catalog_content(workspace, event):
    workspace.reindexObject()
