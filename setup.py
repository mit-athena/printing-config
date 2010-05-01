#!/usr/bin/python

from setuptools import setup, find_packages
from distutils.extension import Extension

try:
    from debian_bundle.changelog import Changelog
    from debian_bundle.deb822 import Deb822
    from email.utils import parseaddr

    version = Changelog(open(path.join(path.dirname(__file__), 'debian/changelog')).read()).\
              get_version().full_version

    maintainer_full = Deb822(open(path.join(path.dirname(__file__), 'debian/control')))['Maintainer']
    maintainer, maintainer_email = parseaddr(maintainer_full)
except:
    version = '0.0.0'
    maintainer = ''
    maintainer_email = ''

setup(
    name="debathena.printing",
    version=version,
    description="Printing configuration for Debathena.",
    maintainer=maintainer,
    maintainer_email=maintainer_email,
    license="MIT",
    packages=find_packages(),
    tests_require=['mox', 'nose>=0.10'],
    setup_requires=['nose>=0.10'],
    dependency_links=['http://code.google.com/p/pymox/downloads/list'],
)
