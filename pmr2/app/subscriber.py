from zope.component import queryUtility, getSiteManager

from pmr2.app.interfaces import IPMR2GlobalSettings
from pmr2.app.content.interfaces import IExposure, IExposureFolder

def catalog_content(obj, event):
    # for the subscriber event.
    obj.reindexObject()

def recursive_recatalog_content(obj, event):
    # for exposure state changes.
    # we are going to be restrictive in what we do.
    obj.reindexObject()
    if IExposure.providedBy(obj) or IExposureFolder.providedBy(obj):
        for id_, subobj in obj.items():
            recursive_recatalog_content(subobj, event)

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

    settings = queryUtility(IPMR2GlobalSettings)
    name = user.getName()
    settings.createUserWorkspaceContainer(name)
