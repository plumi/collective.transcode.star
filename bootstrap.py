##############################################################################
#
# Copyright (c) 2006 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Bootstrap a buildout-based project

Simply run this script in a directory containing a buildout.cfg.
The script accepts buildout command-line options, so you can
use the -c option to specify an alternate configuration file.
"""

import os, shutil, sys, tempfile, urllib2
from optparse import OptionParser

tmpeggs = tempfile.mkdtemp()

# parsing arguments
parser = OptionParser(
    'This is a custom version of the zc.buildout %prog script.  It is '
    'intended to meet a temporary need if you encounter problems with '
    'the zc.buildout 1.5 release.')
parser.add_option("-v", "--version", dest="version", default='1.7.1',
                          help='Use a specific zc.buildout version.  *This '
                          'bootstrap script defaults to '
                          '1.7.1, unlike usual buildpout bootstrap scripts.*')
parser.add_option("-c", None, action="store", dest="config_file",
                   help=("Specify the path to the buildout configuration "
                         "file to be used."))

options, args = parser.parse_args()

if options.eggs:
    eggs_dir = os.path.abspath(os.path.expanduser(options.eggs))
else:
    VERSION = ''

if options.accept_buildout_test_releases:
    args.insert(0, 'buildout:accept-buildout-test-releases=true')

to_reload = False
try:
    import pkg_resources
    if not hasattr(pkg_resources, '_distribute'):
        to_reload = True
        raise ImportError
except ImportError:
    ez = {}
    exec ez_code in ez
    setup_args = dict(to_dir=eggs_dir, download_delay=0)
    if options.download_base:
        setup_args['download_base'] = options.download_base
    if options.use_distribute:
        setup_args['no_fake'] = True
        if sys.version_info[:2] == (2, 4):
            setup_args['version'] = '0.6.32'
    ez['use_setuptools'](**setup_args)
    if 'pkg_resources' in sys.modules:
        reload(sys.modules['pkg_resources'])
    import pkg_resources
    # This does not (always?) update the default working set.  We will
    # do it.
    for path in sys.path:
        if path not in pkg_resources.working_set.entries:
            pkg_resources.working_set.add_entry(path)

ws  = pkg_resources.working_set

requirement = 'distribute'

find_links = options.download_base
if not find_links:
    find_links = os.environ.get('bootstrap-testing-find-links')
if not find_links and options.accept_buildout_test_releases:
    find_links = 'http://downloads.buildout.org/'
if find_links:
    cmd.extend(['-f', quote(find_links)])

cmd = [sys.executable, '-c',
       'from setuptools.command.easy_install import main; main()',
       '-mZqNxd', tmpeggs]

if 'bootstrap-testing-find-links' in os.environ:
    cmd.extend(['-f', os.environ['bootstrap-testing-find-links']])

    def _final_version(parsed_version):
        for part in parsed_version:
            if (part[:1] == '*') and (part not in _final_parts):
                return False
        return True
    index = setuptools.package_index.PackageIndex(
        search_path=[setup_requirement_path])
    if find_links:
        index.add_find_links((find_links,))
    req = pkg_resources.Requirement.parse(requirement)
    if index.obtain(req) is not None:
        best = []
        bestv = None
        for dist in index[req.project_name]:
            distv = dist.parsed_version
            if distv >= pkg_resources.parse_version('2dev'):
                continue
            if _final_version(distv):
                if bestv is None or distv > bestv:
                    best = [dist]
                    bestv = distv
                elif distv == bestv:
                    best.append(dist)
        if best:
            best.sort()
            version = best[-1].version

if version:
    requirement += '=='+version
else:
    requirement += '<2dev'

cmd.append(requirement)

import subprocess
if subprocess.call(cmd, env=env) != 0:
    raise Exception(
        "Failed to execute command:\n%s",
        repr(cmd)[1:-1])

ws.add_entry(tmpeggs)
ws.require('zc.buildout' + VERSION)
import zc.buildout.buildout

# If there isn't already a command in the args, add bootstrap
if not [a for a in args if '=' not in a]:
    args.append('bootstrap')


# if -c was provided, we push it back into args for buildout's main function
if options.config_file is not None:
    args[0:0] = ['-c', options.config_file]

zc.buildout.buildout.main(args)
shutil.rmtree(tmpeggs)
