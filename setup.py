from setuptools import setup, find_packages
import os

version = '0.2'

setup(name='collective.transcode',
      version=version,
      description="Transcoding support for Plone video files, using collective.transcode.daemon",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read() + "\n" +
                       open("AUTHORS.txt").read() + "\n",
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
      packages=find_packages('src/collective.transcode',exclude=['ez_setup']),
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
