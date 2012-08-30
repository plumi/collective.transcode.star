from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.app.layout.viewlets.common import ViewletBase
from collective.transcode.star.interfaces import ITranscodeTool
from zope.component import getUtility
from plone.registry.interfaces import IRegistry


class TranscodeViewlet(ViewletBase):
    render = ViewPageTemplateFile('viewlet.pt')

    def update(self):
        tt = getUtility(ITranscodeTool)
        uid = self.context.UID()

        try:
            self.fieldname = tt[uid].keys()[0]
            self.profiles = tt[uid][tt[uid].keys()[0]]
        except KeyError:
            pass

    def display_size(self):
        size = self.context[self.fieldname].get_size()
        size_kb = size / 1024
        size_mb = size_kb / 1024
        display_size_mb = '{0:n} MB'.format(size_mb) if size_mb > 0 else ''
        display_size_kb = '{0:n} kB'.format(size_kb) if size_kb > 0 else ''
        display_size_bytes = '{0:n} bytes'.format(size)
        display_size = display_size_mb or display_size_kb or display_size_bytes
        return display_size

    def show_subs(self):
        registry = getUtility(IRegistry)
        return registry.get('collective.transcode.star.interfaces.ITranscodeSettings.subtitles', True)
