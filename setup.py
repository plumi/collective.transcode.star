from setuptools import setup, find_packages
import os

version = '0.2'
name = 'collective.transcode'
path = ['src'] + name + name.split('.') + ['version.txt']
version = open(join(*path)).read().strip()
readme = open('README.txt').read()
history = open(join('docs', 'HISTORY.txt')).read()
tests_require = ['collective.monkeypatcher']


setup(name=name,
      version=version,
      description="Transcoding support for Plone video files, using collective.transcode.daemon",
      long_description = readme[readme.find('\n\n'):] + '\n' + history,
      # Get more strings from
      # http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        ],
      keywords='video transcoding plone ffmpeg mp4 ogg',
      author='https://unweb.me',
      author_email='we@unweb.me',
      url='https://svn.plone.org/svn/collective/collective.transcode',
      license='GPL',
      package_dir = {'': 'src/collective.transcode'},
      packages=find_packages('src/collective.transcode/'),
      namespace_packages=['collective'],
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
