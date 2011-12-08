"""The product's interfaces"""
from zope import schema
from zope.interface import Interface
from zope.component.interfaces import IObjectEvent

class ITranscodedEvent(IObjectEvent):
    profile = schema.TextLine(title = u"Transcode profile")


#TODO: add help messages
class ITranscodeSettings(Interface):
    """Transcoding settings"""
    daemon_address = schema.Tuple(title = u'Daemon address',
                                  value_type = schema.TextLine(title = u'address'),
                                  default = (u'http://localhost:8888',),
                                  )

    transcode_profiles = schema.Tuple(title = u'Transcode profiles',
                                      value_type = schema.TextLine(title = u''),
                                      default = (u'jpeg',
                                                 u'webm-low',                                                 
                                                 u'mp4-low',
                                                 u'mp4-high',
                                                 u'webm-high',
                                                ),
                                      )

    portal_types = schema.Tuple(title = u'Portal types to transcode',
                                value_type = schema.TextLine(title = u''),
                                default = (u'File',),
                                )

    mime_types = schema.Tuple(title = u'Supported mime types',
                              value_type = schema.TextLine(title = u''),
                              default = ('application/ogg',
                                        'video/ogg',
                                        'video/x-ogg',
                                        'video/x-ogm+ogg',
                                        'video/flv',
                                        'video/x-flv',
                                        'video/mpeg',
                                        'video/3gpp',
                                        'video/x-ms-wmv',
                                        'video/quicktime',
                                        'video/x-la-asf',
                                        'video/x-ms-asf',
                                        'video/x-msvideo',
                                        'video/mp4',
                                        'video/webm',),
                              )

    secret = schema.TextLine(title = u'Shared secret with transcode daemon(s)',
                             default = u'1771d99931264d538e75eeb19da7d6a0',
                            )

class ITranscodeTool(Interface):
    """TranscodeTool interface"""

    def add(self, obj):
        """add object to transcoding queue if not already there"""

    def status(self, obj, profile, fieldName = None):
        """Check if it is transcoded with given profile"""

    def callback(self, context, request):
        """handle callbacks"""

    def errback(self, context, request):
        """handle errbacks"""

class ICallbackView(Interface):
    """CallbackView interface"""

    def callback_xmlrpc(self, result):
        """callback"""

class ITranscoded(Interface):
    """Marker interface for transcoded content"""

    def url(self, profile):
        """Return the transcoded file url for profile"""
