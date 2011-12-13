from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.app.layout.viewlets.common import ViewletBase
from collective.transcode.star.interfaces import ITranscodeTool
from zope.component import getUtility


class TranscodeViewlet(ViewletBase):
    render = ViewPageTemplateFile('viewlet.pt')

    def update(self):
        tt = getUtility(ITranscodeTool)
        uid = self.context.UID()

        try:
            self.profiles = tt[uid][tt[uid].keys()[0]]
        except KeyError:
            pass
