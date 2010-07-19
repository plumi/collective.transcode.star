from setuptools import setup, find_packages
import os

version = '0.2'
name = 'collective.transcode.star'
path = name.split('.') + ['version.txt']
version = open('/'.join(path)).read().strip()
readme = open('README.txt').read()
history = open('/'.join(['docs', 'HISTORY.txt'])).read()
tests_require = ['collective.monkeypatcher']


setup(name=name,
      version=version,
      description="Transcoding support for Plone video files, using collective.transcode.daemon",
      long_description = readme[readme.find('\n\n'):] + '\n' + history,
      # Get more strings from
      # http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Plone',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Other Audience',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
      ],
      keywords='video transcoding plone ffmpeg mp4 ogg',
      author='https://unweb.me',
      author_email='we@unweb.me',
      url='https://svn.plone.org/svn/collective/collective.transcode.star',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['collective', 'collective.transcode'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          # -*- Extra requirements: -*-
          'plone.app.registry',
          'pycrypto',
          'collective.flowplayer',
          'hashlib'
      ],
      entry_points="""
      # -*- Entry points: -*-

      [z3c.autoinclude.plugin]
      target = plone
      """,
      setup_requires=["PasteScript"],
      paster_plugins=["ZopeSkel"],
      )
