import logging

from plone.app.layout.viewlets.common import ViewletBase
from plone.dexterity.interfaces import IDexterityContent
from plone.registry.interfaces import IRegistry
from plone.uuid.interfaces import IUUID
from zope.component import getUtility

from collective.transcode.star.interfaces import ITranscodeTool

log = logging.getLogger('collective.transcode')


class TranscodeViewlet(ViewletBase):
    def update(self):
        tt = getUtility(ITranscodeTool)
        uid = IUUID(self.context)

        try:
            self.fieldname = tt[uid].keys()[0]
            self.profiles = tt[uid][tt[uid].keys()[0]]
        except KeyError:
            log.warn('No transcode for %s', self.context.absolute_url())

    def display_size(self):
        if IDexterityContent.providedBy(self.context):
            size = getattr(self.context, self.fieldname).getSize()
        else:
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

    def download_original(self):
        if IDexterityContent.providedBy(self.context):
            return '%s/@@download/%s' % (self.context.absolute_url(), self.fieldname)
        else:
            return '%s/at_download/%s' % (self.context.absolute_url(), self.fieldname)
