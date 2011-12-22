from collective.transcode.star.interfaces import ITranscodeTool, ITranscoded, ITranscodedEvent
from hashlib import md5
from zope.app.container.btree import BTreeContainer
import xmlrpclib
from zope.component import getUtility
import urllib
import logging
from plone.registry.interfaces import IRegistry
from persistent.dict import PersistentDict
from collective.transcode.star.crypto import encrypt, decrypt
from Products.CMFCore.utils import getToolByName
from urllib import urlencode
from datetime import datetime
from base64 import b64encode
import transaction
from zope.interface import alsoProvides, noLongerProvides
from StringIO import StringIO
from zope.interface import implements
from zope.component import getSiteManager
from zope.component.interfaces import ObjectEvent
from zope.event import notify

from zope.component import queryUtility
from plone.i18n.normalizer.interfaces import IIDNormalizer

log = logging.getLogger('collective.transcode')

class TranscodeTool(BTreeContainer):
    
    implements(ITranscodeTool)

    def add(self, obj, fieldNames = [], force = False, profiles = []):
        """
           Add a portal object to the transcode queue
        """

        UID = obj.UID()
        # If no fieldNames have been defined as transcodable, then use the primary field
        # TODO: check if they are actually file fields
        if not fieldNames:
            fields = [obj.getPrimaryField()]
        else:
            fields = [obj.getField(f) for f in fieldNames]

        # If file is empty then do nothing
        fileSize = sum([len(f.get(obj).data) for f in fields])
        if not fileSize:
            return
        try:
            address = self.getNextDaemon()
        except Exception, e:
            log.error(u"Can't get daemon address %s" % e)
            return

        try:
            transcodeServer = xmlrpclib.ServerProxy(address)
            daemonProfiles = transcodeServer.getAvailableProfiles()
        except Exception, e:
            log.error(u"Could not connect to transcode daemon %s: %s" % (address, e))
            return

        supported_profiles = self.getProfiles()
        if not profiles:
            profiles = supported_profiles
        else:
            profiles = [p for p in profiles if p in supported_profiles]
            
        secret = self.secret()

        for profile in profiles:
            if profile not in daemonProfiles:
                log.warn(u"profile %s not supported by the transcode daemon at %s" % (profile, address))
                continue
            for field in fields:
                fieldName = field.getName()
                fileType = field.getContentType(obj)
                if fileType not in self.supported_mime_types():
                    log.warn('skipping %s: %s not in %s' %(obj, fileType, self.supported_mime_types()))
                    continue
                data = StringIO(field.get(obj).data)
                md5sum = md5(data.read()).hexdigest()
                # Check if there is already a transcode request pending for the given field and profile
                if self.is_pending(UID, fieldName, profile, md5sum):
                    log.info(u'transcode request already pending for %s:%s:%s:%s' % (UID, fieldName, profile,md5sum))
                    if not force: 
                        continue
                    else:
                        log.info('forcing retranscode')
                if self.is_transcoded(UID, fieldName, profile, md5sum):
                    log.info(u'transcode request already finished for %s:%s:%s:%s' % (UID, fieldName, profile,md5sum))
                    if not force: 
                        continue
                    else:
                        log.info('forcing retranscode')

                portal_url = getToolByName(obj,'portal_url')()
                filePath = obj.absolute_url() 
                fileUrl = portal_url + '/@@serve_daemon'
                fileType = field.getContentType(obj)
                # transliteration of stange filenames
                fileName = field.getFilename(obj)                
                norm = queryUtility(IIDNormalizer)
                fileName = norm.normalize(fileName.decode('utf-8'))

                options = dict()
                input = {
                          'path' : filePath,
                          'url' : fileUrl,
                          'type' : fileType,
                          'fieldName' : fieldNames and fieldName or '', # don't send fieldName if it's the primary field
                          'fileName' : fileName,
                          'uid' : UID,
                        }

                # Transcode request about to be sent. Write it down in the TranscodeTool
                objRec = self.get(UID, None)
                if not objRec:
                    self[UID] = PersistentDict()
                    log.info(u"adding object %s in TranscodeTool" % obj.absolute_url())

                fieldRec = self[UID].get(fieldName, None)
                if not fieldRec: 
                    self[UID][fieldName]=PersistentDict()
                self[UID][fieldName][profile] = PersistentDict({'jobId' : None, 'address' : address, 'status' : 'pending', 'start' : datetime.now(), 'md5' : md5sum})
                
                # We have to commit the transaction to make sure the file can be fetched by the transcode daemon
                transaction.commit()

                # Encrypt and send the transcode request
                input = {'key':b64encode(encrypt(str(input), secret))}
                jobId = transcodeServer.transcode(input, profile, options, portal_url)
                if not jobId or jobId.startswith('ERROR'):
                    log.warn(u'Could not get jobId from daemon %s for profile %s and input %s. Result %s' % (address, profile, input, jobId))
                    self[UID][fieldName][profile]['status'] = jobId or 'failed'
                    continue
                self[UID][fieldName][profile]['jobId'] = jobId

                log.info(u"added profile %s for field %s and content type %s in transcode queue" % ( profile, fieldName, obj.absolute_url()))

        return

    def getProgress(self, jobId):
        """
            Get transcoding progress
        """
        tt = getUtility(ITranscodeTool)
        
        try:
            address = tt.getNextDaemon()
        except Exception, e:
            log.error(u"Can't get daemon address %s" % e)
            return

        try:
            transcodeServer = xmlrpclib.ServerProxy(address)
            progress = transcodeServer.stat(jobId)
        except Exception, e:
            log.error(u"Could not connect to transcode daemon %s: %s" % (address, e))
            return
        return progress
        
    def delete(self, obj, fieldNames = [], force = False):
        '''Pass an xmlrpc call to the daemon when a video is deleted'''

        UID = obj.UID()
        log = logging.getLogger('collective.transcode.star')
        tt = getUtility(ITranscodeTool)

        # If no fieldNames have been defined as transcodable, then use the primary field
        # TODO: check if they are actually file fields
        if not fieldNames:
            fields = [obj.getPrimaryField()]
        else:
            fields = [obj.getField(f) for f in fieldNames]

        # If file is empty then do nothing
        fileSize = sum([len(f.get(obj).data) for f in fields])
        if not fileSize:
            return
        try:
            address = tt.getNextDaemon()
        except Exception, e:
            log.error(u"Can't get daemon address %s" % e)
            return

        try:
            transcodeServer = xmlrpclib.ServerProxy(address)
            daemonProfiles = transcodeServer.getAvailableProfiles()
        except Exception, e:
            log.error(u"Could not connect to transcode daemon %s: %s" % (address, e))
            return

        secret = tt.secret()
        for field in fields:
            fieldName = field.getName()
            if field.getContentType(obj) not in tt.supported_mime_types():
                continue
            data = StringIO(field.get(obj).data)
            md5sum = md5(data.read()).hexdigest()

            portal_url = getToolByName(obj,'portal_url')()
            filePath = obj.absolute_url() 
            fileUrl = portal_url + '/@@serve_daemon'
            fileType = field.getContentType(obj)
            # transliteration of stange filenames
            fileName = field.getFilename(obj)                
            norm = queryUtility(IIDNormalizer)
            fileName = norm.normalize(fileName.decode('utf-8'))

            options = dict()
            input = {
                      'path' : filePath,
                      'url' : fileUrl,
                      'type' : fileType,
                      'fieldName' : fieldNames and fieldName or '', # don't send fieldName if it's the primary field
                      'fileName' : fileName,
                      'uid' : UID,
                    }

            # Encrypt and send the transcode request
            input = {'key':b64encode(encrypt(str(input), secret))}
            transcodeServer.delete(input, options, portal_url)
            tt.__delitem__ ( UID )

        return
   
    def getNextDaemon(self):
        """
           Select the daemon with the minimun queueSize
        """
        registry = getUtility(IRegistry)
        daemons = registry['collective.transcode.star.interfaces.ITranscodeSettings.daemon_address']
        if len(daemons) == 0:
            log.warn(u"No transcode daemons available")
            return

        # Only one daemon available so don't waste any time checking its queue
        if len(daemons) == 1:
            return str(daemons[0])

        # If there are more than one daemons available get the one with the minimum queue size
        min = (-1,None)
        for d in daemons:
            d = str(d)
            try:
                transcodeServer = xmlrpclib.ServerProxy(d)
                queueSize = transcodeServer.queueSize()
                log.info(u"queueSize for daemon %s: %s" % (d, queueSize))
            except Exception, e:
                log.error(u"Could not connect to transcode daemon %s: %s" % (d, e))
                continue
            if queueSize == 0:
                return d
            if min[0] == -1 or queueSize < min[0]:
                min = (queueSize, d)
        return min[1]

    def getProfiles(self):
        """
          Return the list of supported profiles from the registry
        """
        registry = getUtility(IRegistry)
        return registry['collective.transcode.star.interfaces.ITranscodeSettings.transcode_profiles']

    def secret(self):
        registry = getUtility(IRegistry)
        return registry['collective.transcode.star.interfaces.ITranscodeSettings.secret']

    def supported_mime_types(self):        
        registry = getUtility(IRegistry)
        return registry['collective.transcode.star.interfaces.ITranscodeSettings.mime_types']


    def is_pending(self, UID, fieldName, profile, md5sum, timeout=14400):
        """
           Check if the file is already in the transcode queue and has not timed out
        """
        try:
            entry = self[UID][fieldName][profile]
        except Exception, e:
            return False

        if entry['status'] != 'pending' or entry['md5'] != md5sum:
            return False

        if (datetime.now() - entry['start']).seconds < timeout:
            log.warn(u'transcode entry timed out: (%s, %s, %s, %s)' % (UID, fieldName, profile, md5sum))
            return False

        return True
 
    def is_transcoded(self, UID, fieldName, profile, md5sum, timeout=14400):
        """
           Check if the file has already been transcoded
        """
        try:
            entry = self[UID][fieldName][profile]
        except Exception, e:
            return False

        if entry['status'] != 'ok' or entry['md5'] != md5sum or not entry['path']:
            return False

        return True

    def callback(self, result):
        log.info(u"%s callback for %s" % (result['profile'], result['UID']))
        (obj, entry) = self.validate(result)
        if not obj or not entry:
            return
        if entry['status'] != 'pending':
            log.warn('entry status was not pending, that should not happen: %s' % entry) 
        entry['path'] = result['path']
        entry['end'] = datetime.now()
        entry['status'] = 'ok'
        alsoProvides(obj, ITranscoded)
        notify(TranscodedEvent(obj, result['profile']))
        try:
            obj.reindexObject(idxs=['object_provides'])
        except Exception, e:
            pass
        return

    def errback(self, result):
        log.info(u"%s errback for %s" % (result['profile'], result['UID']))
        (obj, entry) = self.validate(result)
        if not obj or not entry:
            return
        if entry['status'] != 'pending':
            log.warn('entry status was not pending, that should not happen: %s' % entry)
        entry['end'] = datetime.now()
        entry['status'] = result['msg']
        return

    def validate(self, result):
        """
           Validate the result of callbacks and errbacks
        """
        portal = getSiteManager()
        uid_catalog = getToolByName(portal, 'uid_catalog')
        try:
            obj = uid_catalog(UID=result['UID'])[0].getObject()
        except Exception, e:
            log.error("Can't get object with UID from the uid_catalog: %s" % e)
            return (False, False)

        fieldName = result['fieldName'] or obj.getPrimaryField().getName()

        record = self.get(result['UID'], None)
        if record is None:
            log.error("No records for UID %s in TranscodeTool" % result['uid'])
            return (obj, False)

        try:
            entry = record[fieldName][result['profile']]
        except Exception, e:
            log.error("No entry for fieldName %s and profile %s" % (fieldName, result['profile']))
            log.error("Existing entries for object: %s" % record)
            return (obj, False)

        return (obj, entry)

    def status(self, obj, profile, fieldName = None):
        """Check if it is transcoded with given profile"""
        if not fieldName:
            fieldName = obj.getPrimaryField().getName()
        try:
            return self[obj.UID()][fieldName][profile]['status']
        except Exception, e:
            return False            

class TranscodedEvent(ObjectEvent):

    implements(ITranscodedEvent)

    def __init__(self, object, profile):
        self.object = object
        self.profile = profile
