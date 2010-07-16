from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.app.layout.viewlets.common import ViewletBase
from collective.transcode.interfaces import ITranscodeTool
from zope.component import getUtility

class TranscodeViewlet(ViewletBase):
    render = ViewPageTemplateFile('viewlet.pt')

    def update(self):
        tt = getUtility(ITranscodeTool)
        try:
            self.mp4 = tt[self.context.UID()][tt[self.context.UID()].keys()[0]]['mp4']
            self.jpeg = tt[self.context.UID()][tt[self.context.UID()].keys()[0]]['jpeg']
        except:
            pass
