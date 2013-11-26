from base64 import b64encode, b64decode
import logging

from AccessControl import getSecurityManager
from AccessControl.SecurityManagement import newSecurityManager
from plone.app.uuid.utils import uuidToObject
from plone.app.blob.download import handleRequestRange
from plone.app.blob.iterators import BlobStreamIterator
from plone.dexterity.interfaces import IDexterityContent
from plone.registry.interfaces import IRegistry
from plone.rfc822.interfaces import IPrimaryFieldInfo
from plone.uuid.interfaces import IUUID
from Products.Five.browser import BrowserView
from Products.CMFCore.utils import getToolByName
from zope.interface import implements
from zope.component import getUtility

from collective.transcode.star.crypto import encrypt, decrypt
from collective.transcode.star.interfaces import ICallbackView, ITranscodeTool

try:
    from collective.transcode.burnstation.interfaces import IBurnTool
    BURNSTATION_SUPPORT=True
except ImportError:
    BURNSTATION_SUPPORT=False

log = logging.getLogger('collective.transcode')


class EmbedView(BrowserView):
    """
        Embedded video vew
    """
    def jpeg(self):
        tt = getUtility(ITranscodeTool)
        uid = IUUID(self.context)
        try:
            return tt[uid][tt[uid].keys()[0]]['jpeg']['address'] + '/' + \
                tt[uid][tt[uid].keys()[0]]['jpeg']['path']
        except:
            return False

    def profiles(self):
        tt = getUtility(ITranscodeTool)
        uid = IUUID(self.context)
        try:
            return tt[uid][tt[uid].keys()[0]]
        except:
            return []

    def canDownload(self):
        registry = getUtility(IRegistry)
        return registry.get('collective.transcode.star.interfaces.ITranscodeSettings.showDownload', True)


class CallbackView(BrowserView):
    """
        Handle callbacks and errbacks from transcode daemon
    """
    implements(ICallbackView)
    def callback_xmlrpc(self, result):
        """
           Handle callbacks
        """
        tt = getUtility(ITranscodeTool)
        secret = tt.secret()
        try:
            result = eval(decrypt(b64decode(result['key']), secret), {"__builtins__":None},{})
            assert result.__class__ is dict
        except Exception as e:
            log.error("Unauthorized callback %s" % result)
            return

        if result['profile'] == 'iso' and BURNSTATION_SUPPORT:
            bt = getUtility(IBurnTool)
            if result['path']:
                bt.callback(result)
            else:
                bt.errback(result)
        else:
            if result['path']:
                tt.callback(result)
            else:
                tt.errback(result)


class ServeDaemonView(BrowserView):
    """
        Handle callbacks from transcode daemon
    """
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        try:
            tt = getUtility(ITranscodeTool)
            key = self.request['key']
            input = decrypt(b64decode(key), tt.secret())
            (uid, self.fieldName, profile) = eval(input, {"__builtins__":None}, {})
            pm = getToolByName(self.context, 'portal_membership')
            newSecurityManager(self.request,
                               pm.getMemberById(self.context.getOwner().getId()))
            obj = uuidToObject(uid)
            if obj is None:
                log.error('No object for UUID %s', uid)
                return
            field = self._getField(obj)
            if field is None:
                return
            if tt[uid][self.fieldName][profile]['status']!='pending':
                log.error('status not pending')
                raise
            return self._getFile(obj, field)
        except Exception as e:
            log.error('Unauthorized file request: %s' % e)
            return

    def _getField(self, obj):
        if IDexterityContent.providedBy(obj):
            return self._getDexterityField(obj)
        else:
            return self._getArchetypeField(obj)

    def _getDexterityField(self, obj):
        field = None
        if not self.fieldName:
            try:
                primary = IPrimaryFieldInfo(obj)
                self.fieldName = primary.fieldname
                field = primary.field
            except TypeError:
                log.error('No field specified and no primary field.')
        else:
            try:
                field = getattr(obj, self.fieldName)
            except AttributeError:
                log.error('No field %s on object %s.' % (self.fieldName, obj))
        return field

    def _getArchetypeField(self, obj):
        if not self.fieldName:
            self.fieldName = obj.getPrimaryField().getName()
        return obj.getField(self.fieldName)

    def _getFile(self, obj, field):
        if IDexterityContent.providedBy(obj):
            return self._getDexterityFile(obj, field)
        else:
            return self._getArchetypeFile(obj, field)

    def _getDexterityFile(self, obj, field):
        self.request.response.setHeader('Accept-Ranges', 'bytes')
        self.request.response.setHeader("Content-Length", field.getSize())
        self.request.response.setHeader('Content-Type', field.contentType)
        request_range = handleRequestRange(
            obj,
            field.getSize(),
            self.request,
            self.request.response
            )
        return BlobStreamIterator(field, **request_range)

    def _getArchetypeFile(self, obj, field):
        if field.getFilename(obj).__class__ is unicode:
            # Monkey patch the getFilename to go around plone.app.blob unicode filename bug
            def getFilenameAsString(obj):
                return field.oldGetFilename(obj).encode(obj.getCharset(), 'ignore')
            field.oldGetFilename = field.getFilename
            field.getFilename = getFilenameAsString
            dl = field.download(obj)
            field.getFilename = field.oldGetFilename
            del field.oldGetFilename
            return dl
        else:
            return field.download(obj)
