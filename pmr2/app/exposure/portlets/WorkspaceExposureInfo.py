from zope import schema
from zope.formlib import form
from zope.interface import implements
import zope.component

from plone.app.portlets.portlets import base
from plone.portlets.interfaces import IPortletDataProvider
from plone.app.portlets.cache import render_cachekey
from plone.memoize.view import memoize

from Acquisition import aq_inner, aq_parent
from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFCore.utils import getToolByName

from pmr2.app.interfaces import *
from pmr2.app.workspace.interfaces import IWorkspace
from pmr2.app.exposure.interfaces import *
from pmr2.app.exposure.browser.browser import ViewPageTemplateFile


class IWorkspaceExposureInfoPortlet(IPortletDataProvider):
    """\
    Exposure Information portlet.
    """


class Assignment(base.Assignment):
    implements(IWorkspaceExposureInfoPortlet)

    def __init__(self):
        pass

    @property
    def title(self):
        return _(u"Workspace's Exposure Info")


class Renderer(base.Renderer):
    _template = ViewPageTemplateFile('workspace_exposure_info.pt')

    def __init__(self, *args):
        base.Renderer.__init__(self, *args)
        self.title = u"Workspace's Exposure Info"
        if self.available:
            pass

    @memoize
    def portal_url(self):
        portal = getToolByName(self.context, 'portal_url').getPortalObject()
        return portal.absolute_url()

    @property
    def available(self):
        isworkspace = IWorkspace.providedBy(self.context)
        exposurelayer = IPMR2ExposureLayer.providedBy(self.request)
        return isworkspace and exposurelayer

    def render(self):
        return self._template()


class AddForm(base.AddForm):
    form_fields = form.Fields(IWorkspaceExposureInfoPortlet)
    label = _(u"Add Workspace's Exposure Info")
    description = _(u"This portlet searches the catalog for the latest exposure for this workspace.")

    def create(self, data):
        return Assignment()


class EditForm(base.EditForm):
    form_fields = form.Fields(IWorkspaceExposureInfoPortlet)
    label = _(u"Edit Workspace's Exposure Info")
    description = _(u"This portlet searches the catalog for the latest exposure for this workspace.")
