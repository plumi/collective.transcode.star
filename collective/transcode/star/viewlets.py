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
            self.mp4 = tt[uid][tt[uid].keys()[0]]['mp4']
        except KeyError:
            pass
        
        try:
            self.webm = tt[uid][tt[uid].keys()[0]]['webm']
        except KeyError:
            pass
        
        try:
            self.jpeg = tt[uid][tt[uid].keys()[0]]['jpeg']
        except KeyError:
            pass
