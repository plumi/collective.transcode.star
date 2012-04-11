from setuptools import setup, find_packages
import os

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

name = 'collective.transcode.star'
version = '0.16'

long_description = (
    read('README.txt')
    + '\n' +
    'Contributors\n'
    '~~~~~~~~~~~~\n'
    + '\n' +
    read('docs/CONTRIBUTORS.txt')
    + '\n' +
    read('docs/HISTORY.txt')
    + '\n' +
   'Download\n'
   '--------\n'
    )

setup(name=name,
      version=version,
      description="Transcoding support for Plone video files, using collective.transcode.daemon",
      long_description = long_description,
      # Get more strings from
      # http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers = [
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
      keywords='video transcoding plone ffmpeg flv mp4 ogg',
      author='https://unweb.me',
      author_email='we@unweb.me',
      url='https://github.com/plumi/collective.transcode.star',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['collective', 'collective.transcode'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          # -*- Extra requirements: -*-
          'plone.app.registry',
          'collective.mediaelementjs',
          'pycrypto',
      ],
      entry_points="""
      # -*- Entry points: -*-

      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
