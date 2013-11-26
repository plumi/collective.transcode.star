from base64 import b64encode
from datetime import datetime, timedelta
from hashlib import md5
import logging
import pytz
import transaction
import urllib
from urllib import urlencode
import xmlrpclib

from AccessControl.SecurityManagement import newSecurityManager
from persistent.dict import PersistentDict
from plone.app.async.interfaces import IAsyncService
from plone.app.uuid.utils import uuidToObject
from plone.dexterity.interfaces import IDexterityContent
from plone.i18n.normalizer.interfaces import IIDNormalizer
from plone.uuid.interfaces import IUUID
from plone.registry.interfaces import IRegistry
from plone.rfc822.interfaces import IPrimaryFieldInfo
from Products.CMFCore.utils import getToolByName
from StringIO import StringIO
from zope.component import queryUtility, getUtility
from zope.component import getSiteManager
from zope.component.interfaces import ObjectEvent
from zope.container.btree import BTreeContainer
from zope.event import notify
from zope.interface import alsoProvides, noLongerProvides
from zope.interface import implements

from collective.transcode.star.crypto import encrypt, decrypt
from collective.transcode.star.interfaces import ITranscodeTool, ITranscoded,\
    ITranscodedEvent

log = logging.getLogger('collective.transcode')
SETTING_DAEMON_ADDRESS = 'collective.transcode.star.interfaces.ITranscodeSettings.daemon_address'
SETTING_PROFILES = 'collective.transcode.star.interfaces.ITranscodeSettings.transcode_profiles'
SETTING_SECRET = 'collective.transcode.star.interfaces.ITranscodeSettings.secret'
SETTING_MIME_TYPES = 'collective.transcode.star.interfaces.ITranscodeSettings.mime_types'


def transcode_request(obj, fieldName, UID, payload, secret, address,
                      profile, options, portal_url):
    "Encrypt and send the transcode request"
    try:
        transcodeServer = xmlrpclib.ServerProxy(address, allow_none=True)
    except Exception, e:
        log.error(u"Could not connect to transcode daemon %s: %s"
                  % (address, e))
        return
    payload = {'key':b64encode(encrypt(str(payload), secret))}
    jobId = transcodeServer.transcode(payload, profile, options, portal_url)
    tt = getUtility(ITranscodeTool)
    if not jobId or jobId.startswith('ERROR'):
        log.warn(u'Could not get jobId from daemon %s for profile %s'
                 u'and input %s. Result %s'
                 % (address, profile, payload, jobId))
        tt[UID][fieldName][profile]['status'] = jobId or 'failed'
    tt[UID][fieldName][profile]['jobId'] = jobId
    log.info(u"added profile %s for field %s and"
             u"content type %s in transcode queue"
             % ( profile, fieldName, obj.absolute_url()))


class TranscodeTool(BTreeContainer):
    def add(self, obj, fieldNames=[], force=False, profiles=[]):
        """
           Add a portal object to the transcode queue
        """
        UID = IUUID(obj)

        fields = self._getFields(obj, fieldNames)
        if not self._hasFiles(obj, fields):
            return
        address = self._getDaemonAddress()
        if address is None:
            return
        (transcodeServer, daemonProfiles) = self._getDaemon(address)
        if transcodeServer is None or daemonProfiles is None:
            return
        profiles = self._getProfiles(profiles)
        secret = self.secret()

        for profile in profiles:
            if profile not in daemonProfiles:
                log.warn(u"profile %s not supported by the transcode daemon at %s"
                         % (profile, address))
                continue
            for field in fields:
                info = self._getFieldInfo(obj, field)
                if info is None:
                    continue
                fieldName = info['fieldName']
                md5sum = info['md5sum']
                fileType = info['fileType']
                # Check if there is already a transcode request pending
                # for the given field and profile
                if self.is_pending(UID, fieldName, profile, md5sum):
                    log.info(u'transcode request already pending for %s:%s:%s:%s'
                             % (UID, fieldName, profile, md5sum))
                    if not force:
                        continue
                    else:
                        log.info('forcing retranscode')
                if self.is_transcoded(UID, fieldName, profile, md5sum):
                    log.info(u'transcode request already finished for %s:%s:%s:%s'
                             % (UID, fieldName, profile, md5sum))
                    if not force:
                        continue
                    else:
                        log.info('forcing retranscode')

                self._sendRequest(
                    fieldNames and fieldName or '',
                    md5sum, secret, address, profile, fieldName,
                    obj, UID, fileType, info['fileName']
                    )
        return

    def _sendRequest(self, fieldNames, md5sum, secret, address, profile,
                     fieldName, obj, UID, fileType, fileName):
        portal_url = getToolByName(obj, 'portal_url')()
        filePath = obj.absolute_url()
        fileUrl = portal_url + '/@@serve_daemon'
        # transliteration of strange filenames
        norm = queryUtility(IIDNormalizer)
        fileName = norm.normalize(fileName.decode('utf-8'))
        payload = {
            'path' : filePath,
            'url' : fileUrl,
            'type' : fileType,
            # don't send fieldName if it's the primary field
            'fieldName' : fieldNames,
            'fileName' : fileName,
            'uid' : UID,
            }

        # Transcode request about to be sent. Write it down in the TranscodeTool
        if not self.get(UID, None):
            self[UID] = PersistentDict()
            log.info(u"adding object %s in TranscodeTool"
                     % obj.absolute_url())
        if not self[UID].get(fieldName, None):
            self[UID][fieldName] = PersistentDict()
        self[UID][fieldName][profile] = PersistentDict({
                'jobId' : None,
                'address' : address,
                'status' : 'pending',
                'start' : datetime.now(),
                'md5' : md5sum
                })
        async = getUtility(IAsyncService)
        temp_time = datetime.now(pytz.UTC) + timedelta(seconds=2)
        options = dict()
        job = async.queueJobWithDelay(None, temp_time,
                                      transcode_request, obj, fieldName,
                                      UID, payload, secret, address,
                                      profile, options, portal_url)

    def _getFields(self, obj, fieldNames):
        # If no fieldNames have been defined as transcodable,
        # then use the primary field
        # TODO: check if they are actually file fields

        fields = []
        if IDexterityContent.providedBy(obj):
            if not fieldNames:
                try:
                    primary = IPrimaryFieldInfo(obj)
                    fields = [(primary.fieldname, primary.field)]
                except TypeError:
                    log.error('No field specified and no primary field.')
            else:
                for f in fieldNames:
                    try:
                        fields.append((f, getattr(obj, f)))
                    except AttributeError:
                        log.error('No field %s on object %s.' % (f, obj))
        else:
            if not fieldNames:
                fields = [obj.getPrimaryField()]
            else:
                fields = [obj.getField(f) for f in fieldNames]
        return fields

    def _hasFiles(self, obj, fields):
        # If file is empty then do nothing
        if IDexterityContent.providedBy(obj):
            fileSize = sum([f[1].getSize() for f in fields])
        else:
            fileSize = sum([len(f.get(obj).data) for f in fields])
        return fileSize != 0

    def _getFieldInfo(self, obj, field):
        if IDexterityContent.providedBy(obj):
            fieldName = field[0]
            fileType = field[1].contentType
            md5sum = md5(field[1].data).hexdigest()
            fileName = field[1].filename
        else:
            fieldName = field.getName()
            fileType = field.getContentType(obj)
            data = StringIO(field.get(obj).data)
            md5sum = md5(data.read()).hexdigest()
            fileName = field.getFilename(obj)
        if fileType not in self.supported_mime_types():
            log.warn('skipping %s: %s not in %s'
                     % (obj, fileType, self.supported_mime_types()))
            return None
        return {
            'fieldName': fieldName,
            'fileType': fileType,
            'md5sum': md5sum,
            'fileName': fileName
            }

    def _getProfiles(self, profiles):
        supported_profiles = self.getProfiles()
        if not profiles:
            profiles = supported_profiles
        else:
            profiles = [p for p in profiles if p in supported_profiles]
        return profiles

    def _getDaemonAddress(self):
        try:
            address = self.getNextDaemon()
        except Exception, e:
            log.error(u"Can't get daemon address %s" % e)
            return
        return address

    def _getDaemon(self, address):
        try:
            transcodeServer = xmlrpclib.ServerProxy(address)
            daemonProfiles = transcodeServer.getAvailableProfiles()
        except Exception, e:
            log.error(u"Could not connect to transcode daemon %s: %s"
                      % (address, e))
            return (None, None)
        return (transcodeServer, daemonProfiles)

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
            log.error(u"Could not connect to transcode daemon %s: %s"
                      % (address, e))
            return
        return progress

    def delete(self, obj, fieldNames = [], force = False):
        '''Pass an xmlrpc call to the daemon when a video is deleted'''
        UID = IUUID(obj)
        log = logging.getLogger('collective.transcode.star')
        tt = getUtility(ITranscodeTool)
        fields = self._getFields(obj, fieldNames)
        if not self._hasFiles(obj, fields):
            return
        address = self._getDaemonAddress()
        if address is None:
            return
        (transcodeServer, daemonProfiles) = self._getDaemon(address)
        if transcodeServer is None or daemonProfiles is None:
            return
        secret = self.secret()

        for field in fields:
            info = self._getFieldInfo(obj, field)
            if info is None:
                continue
            fieldName = info['fieldName']
            md5sum = info['md5sum']
            fileType = info['fileType']
            fileName = info['fileName']
            filePath = obj.absolute_url()
            portal_url = getToolByName(obj,'portal_url')()
            fileUrl = portal_url + '/@@serve_daemon'
            norm = queryUtility(IIDNormalizer)
            fileName = norm.normalize(fileName.decode('utf-8'))

            options = dict()
            payload = {
                'path' : filePath,
                'url' : fileUrl,
                'type' : fileType,
                # don't send fieldName if it's the primary field
                'fieldName' : fieldNames and fieldName or '',
                'fileName' : fileName,
                'uid' : UID,
                }
            # Encrypt and send the transcode request
            payload = {'key':b64encode(encrypt(str(payload), secret))}
            transcodeServer.delete(payload, options, portal_url)
            tt.__delitem__(UID)
        return

    def getNextDaemon(self):
        """
           Select the daemon with the minimun queueSize
        """
        registry = getUtility(IRegistry)
        daemons = registry[SETTING_DAEMON_ADDRESS]
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
        return registry[SETTING_PROFILES]

    def secret(self):
        registry = getUtility(IRegistry)
        return registry[SETTING_SECRET]

    def supported_mime_types(self):
        registry = getUtility(IRegistry)
        return registry[SETTING_MIME_TYPES]


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
            log.warn(u'transcode entry timed out: (%s, %s, %s, %s)'
                     % (UID, fieldName, profile, md5sum))
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

        if entry['status'] != 'ok' or entry['md5'] != md5sum\
                or not entry['path']:
            return False

        return True

    def callback(self, result):
        log.info(u"%s callback for %s" % (result['profile'], result['UID']))
        (obj, entry) = self.validate(result)
        if not obj or not entry:
            return
        if entry['status'] != 'pending':
            log.warn('entry status was not pending, that should not happen: %s'
                     % entry)
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
            log.warn('entry status was not pending, that should not happen: %s'
                     % entry)
        entry['end'] = datetime.now()
        entry['status'] = result['msg']
        return

    def validate(self, result):
        """
           Validate the result of callbacks and errbacks
        """
        portal = getSiteManager()
        #FIX errors introduced with Plone Hotfix 20130618
        pm = getToolByName(portal, 'portal_membership')
        newSecurityManager(portal, pm.getMemberById(portal.getOwner().getId()))
        obj = uuidToObject(result['UID'])
        if obj is None:
            log.error("Can't get object with UUID")
            return (False, False)
        fieldName = self._getFieldName(obj, result['fieldName'])
        if fieldName is None:
            return (obj, False)
        record = self.get(result['UID'], None)
        if record is None:
            log.error("No records for UID %s in TranscodeTool" % result['uid'])
            return (obj, False)
        try:
            entry = record[fieldName][result['profile']]
        except Exception, e:
            log.error("No entry for fieldName %s and profile %s"
                      % (fieldName, result['profile']))
            log.error("Existing entries for object: %s" % record)
            return (obj, False)
        return (obj, entry)

    def _getFieldName(self, obj, fieldName):
        if fieldName:
            return fieldName
        if IDexterityContent.providedBy(obj):
            try:
                primary = IPrimaryFieldInfo(obj)
                return primary.fieldname
            except TypeError:
                log.error('No field specified and no primary field.')
                return None
        else:
            return obj.getPrimaryField().getName()

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
