Introduction
============
collective.transcode.* or transcode.star for short, is a suite of modules 
that provide transcoding services to Plone sites.

The naming scheme has been inspired from collective.blog.star, with which
transcode.star also shares some basic principles:

 * Be modular. Not everyone wants everything your software has to offer.
 * Be flexible. Don't assume that people want to use your software in one particular way.
 * Be simplistic. If there is a simple way of doing it, do it that way.
 * Be Ploneish. Plone already has 90% of what we need built in. Use it.

Out of the box, it works with standard Plone Files. It will be triggered when
 uploading video content which will then be transcoded to mp4 and ogv format. 
Additionally, a jpeg thumbnail will be extracted from the 5th second of the 
videos and a flowplayer viewlet pointing to the mp4 file will be displayed 
inside the IAboveContentBody viewlet manager.

Transcode.star can be easily configured through the Plone Control Panel, to 
work with any custom AT content type, as long as there is a File field. Just 
got to the Transcode Settings panel and enter a new entry in the supported 
portal_types in the form of YourCustomATName:yourFileFieldNameSupport 

Support for Dexterity content types is planned for future versions

For the transcoding to work you need to start the transcodedaemon instance 
provided in the buildout.

If you transcoding needs are high, you can configure several transcode 
daemons. You site will select the daemon with the minimum queue length.

All communication between transcode.star and transcode.daemon is encrypted.


Requirements
============
Apart from what is assembled by the buildout, the following dependencies must
be installed manually for the transcoding scripts to work:

 * ffmpeg with x264 support
 * ffmpeg2theora

In Ubuntu 10.04 you can install the above using the following commands:

    sudo wget --output-document=/etc/apt/sources.list.d/medibuntu.list http://www.medibuntu.org/sources.list.d/$(lsb_release -cs).list && sudo apt-get --quiet update && sudo apt-get --yes --quiet --allow-unauthenticated install medibuntu-keyring && sudo apt-get --quiet update

    sudo aptitude install build-essential libavcodec-unstripped-52 ffmpeg ffmpeg2theora


Installation
============
For production deployments make sure you change the secret key in your buildout.cfg

Plone 4.x
~~~~~~~~~

    python2.6 bootstrap.py
    ./bin/buildout

Plone 3.x
~~~~~~~~~

    python2.4 bootstrap.py -c buildout-p3.cfg
    ./bin/buildout -c buildout-p3.cfg


Usage
=====
Start the transcode daemon:

    ./bin/transcodedaemon start # or fg to start it in the foreground

Start Zope:

    ./bin/instance start

Add a new Plone site, go to the Install Products Form and install transcode.star
A new control panel screen called "Transcode Settings" will be available. You 
can use it to configure the supported profiles, the supported mime_types and the
portal_types and respective fields that you need transcoding for. If you have 
changed the secret key in your buildout make sure you enter the new key here as
well.

Then simply add a new object (File by default) and upload a file with a 
mimetype in the supported mimetypes. If you are running transcodedaemon and 
zope in the foreground you will be able to see the transcoding process taking 
place. When the transcoding is complete, refresh your content type's view page
 and you should see a flowplayer instance above your content loaded with the mp4
version of your video.

Authors
=======
Unweb.me, https://unweb.me
 
