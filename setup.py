import ez_setup
ez_setup.use_setuptools()

from setuptools import setup, find_packages

exec(open('EGFScheduler/version.py').read()) # loads __version__

setup(name='EGFScheduler',
      version=__version__,
      author='Valentin',
    description='',
    long_description=open('README.rst').read(),
    license='see LICENSE.txt',
    keywords="",
    packages= find_packages(exclude='docs'))
