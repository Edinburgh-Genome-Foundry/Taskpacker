import ez_setup
ez_setup.use_setuptools()

from setuptools import setup, find_packages

exec(open('taskpacker/version.py').read()) # loads __version__

setup(
    name='taskpacker',
    version=__version__,
    author='Valentin',
    description='',
    long_description=open('README.rst').read(),
    license='MIT',
    keywords="",
    packages=find_packages(exclude='docs'),
    install_requires=['Numberjack', 'numpy'])
