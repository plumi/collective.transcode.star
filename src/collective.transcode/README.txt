Introduction
============

collective.transcode is a Plone product that offers transcoding services
for Archetypes content. It works out of the box with standard Plone Files, 
providing transcoding to mp4 and ogv for video files. Additionally, it can be
configured through the Plone Control Panel, to work with any custom AT content
type. 

The media transcoding and serving are done by one or more collective.transcode.daemon instances, which are intelligently load balanced by collective.transcode.

Requirements
============
ffmpeg with x264 support
ffmpeg2theora

Installation (Ubuntu 10.04)
===========================
sudo wget --output-document=/etc/apt/sources.list.d/medibuntu.list http://www.medibuntu.org/sources.list.d/$(lsb_release -cs).list && sudo apt-get --quiet update && sudo apt-get --yes --quiet --allow-unauthenticated install medibuntu-keyring && sudo apt-get --quiet update

sudo aptitude install build-essential libavcodec-unstripped-52 ffmpeg ffmpeg2theora
