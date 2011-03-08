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
                                      default = (u'jpeg', u'mp4', u'ogg', u'3gp' u'iphone',),
                                      )

    portal_types = schema.Tuple(title = u'Portal types to transcode', 
                                value_type = schema.TextLine(title = u''),
                                default = (u'File',),
                                )

    mime_types = schema.Tuple(title = u'Supported mime types',
                              value_type = schema.TextLine(title = u''),
                              default = (u'video/3gpp', u'video/x-ms-wmv', 
                                         u'video/ogg', u'video/x-ogg', u'video/x-ogm+ogg', 
                                         u'video/mpeg', u'video/quicktime', u'video/x-la-asf', 
                                         u'video/x-ms-asf', u'video/x-msvideo', u'video/mp4',
                                         u'video/flv', u'video/x-flv',),
                              )

    secret = schema.TextLine(title = u'Shared secret with transcode daemon(s)',
                             default = u'1771d99931264d538e75eeb19da7d6a0',
                            )
    html5 = schema.Choice(title = u'Choose video embed method',
				description=u"Choose if you would like to use just the HTML5 video tag, or Flash (Flowplayer) or if you would like to use HTML5 with Flowplayer as failback for browsers that don't support the HTML5 video tag",
				values = ['Flash - Flowplayer'],
				default = "Flash - Flowplayer",
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
