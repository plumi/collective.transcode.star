"""Event subscribers"""
import logging
import transaction

from plone.dexterity.interfaces import IDexterityContent
from plone.registry.interfaces import IRegistry
from plone.uuid.interfaces import IUUID
from Products.CMFCore.interfaces import IContentish
from Products.CMFCore.interfaces._content import IContentish
from zope.component import adapter
from zope.component import getUtility
from zope.component import queryUtility
from zope.component import getSiteManager
from zope.component.interfaces import ObjectEvent
from zope.interface.interfaces import IInterface
from zope.lifecycleevent.interfaces import IObjectModifiedEvent
from zope.lifecycleevent.interfaces import IObjectCreatedEvent
from zope.lifecycleevent.interfaces import IObjectAddedEvent

from collective.transcode.star.interfaces import ITranscodeTool, ITranscodedEvent

log = logging.getLogger('collective.transcode')
SETTING_TYPES = 'collective.transcode.star.interfaces.ITranscodeSettings.portal_types'


def is_transcode_installed(object):
    return queryUtility(ITranscodeTool, default=False)


@adapter(IContentish, IObjectCreatedEvent)
def addFile(obj, event):
    editFile(obj, event)


@adapter(IDexterityContent, IObjectAddedEvent)
def addDexterityFile(obj, event):
    editFile(obj, event)


@adapter(IContentish, IObjectModifiedEvent)
def editFile(obj, event):
    if is_transcode_installed(obj) is False:
        return
    if not IUUID(obj, None):
        return
    try:
        registry = getUtility(IRegistry)
        types = registry[SETTING_TYPES]
        newTypes = [t.split(':')[0] for t in types]
        if unicode(obj.portal_type) not in newTypes:
            return
        fieldNames = [str(t.split(':')[1]) for t in types
                      if ('%s:' % unicode(obj.portal_type)) in t]
        tt = getUtility(ITranscodeTool)
        tt.add(obj, fieldNames)
    except Exception, e:
        log.error("Could not transcode resource %s\n Exception: %s"
                  % (obj.absolute_url(), e))


@adapter(IDexterityContent, ITranscodedEvent)
def changeDexterityLayout(obj, event):
    changeLayout(obj, event)


@adapter(IContentish, ITranscodedEvent)
def changeLayout(obj, event):
    if obj.getLayout() == 'mediaelementjs':
        obj.setLayout('file_view')


def deleteTranscodedVideos(obj, event):
   if is_transcode_installed(obj) is False:
        return
   if not IUUID(obj, None):
        return
   try:
        registry = getUtility(IRegistry)
        types = registry[SETTING_TYPES]
        newTypes = [t.split(':')[0] for t in types]
        if unicode(obj.portal_type) not in newTypes:
            return
        fieldNames = [str(t.split(':')[1]) for t in types
                      if ('%s:' % unicode(obj.portal_type)) in t]
        tt = getUtility(ITranscodeTool)
        request = getattr(obj, 'REQUEST', None)
        if 'form.submitted' in request.form:
            tt.delete(obj, fieldNames)
        #delete video only after confirmation for delete is clicked
   except Exception, e:
        log.error("Could not delete resource %s\n Exception: %s"
                  % (obj.absolute_url(), e))
