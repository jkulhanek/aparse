from setuptools import setup, find_packages
from aparse import __version__

setup(
    name='aparse',
    version=__version__,
    packages=find_packages(include=('aparse', 'aparse.*')),
    author='Jonáš Kulhánek',
    author_email='jonas.kulhanek@live.com',
    license='MIT License',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    install_requires=[x.rstrip('\n') for x in open('requirements.txt')])
