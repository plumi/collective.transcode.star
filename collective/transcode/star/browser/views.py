from Products.Five.browser import BrowserView
from collective.transcode.star.interfaces import ICallbackView, ITranscodeTool
from zope.interface import implements
from zope.component import getUtility
from collective.transcode.star.crypto import encrypt, decrypt
from base64 import b64encode, b64decode
import logging

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
        uid = self.context.UID()
        try:
            return tt[uid][tt[uid].keys()[0]]['jpeg']['address'] + '/' + \
                    tt[uid][tt[uid].keys()[0]]['jpeg']['path']
        except:
            return False
        
    
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
            (uid, fieldName, profile) = eval(input, {"__builtins__":None},{})
            obj = self.context.uid_catalog(UID=uid)[0].getObject()
            if not fieldName:
                fieldName = obj.getPrimaryField().getName()
            field = obj.getField(fieldName)
            if tt[uid][fieldName][profile]['status']!='pending':
                log.error('status not pending')
                raise
            if field.getFilename(obj).__class__ is unicode:
                # Monkey patch the getFilename to go around plone.app.blob unicode filename bug
                def getFilenameAsString(obj):
                    return field.oldGetFilename(obj).encode(obj.getCharset(),'ignore')
                field.oldGetFilename = field.getFilename
                field.getFilename = getFilenameAsString
                dl = field.download(obj)
                field.getFilename = field.oldGetFilename
                del field.oldGetFilename
                return dl
            else:
                return field.download(obj)
        except Exception as e:
            log.error('Unauthorized file request: %s' % e)
            return
