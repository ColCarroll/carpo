from codecs import open
from os import path
from setuptools import setup, find_packages
import sys

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as buff:
    long_description = buff.read()

if sys.version_info < (3, 4):
    ipython_req = 'ipython<6.0'
else:
    ipython_req = 'ipython'


setup(
    name='carpo',
    version='0.3',
    description='Run, profile, and save Jupyter notebooks from the command line',
    long_description=long_description,
    author='Colin Carroll',
    author_email='colcarroll@gmail.com',
    url='https://github.com/ColCarroll/carpo',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    packages=find_packages(exclude=['test']),
    install_requires=[
        'Click>=6.7',
        'GitPython>=2.1.3',
        'ipykernel',
        ipython_req,
        'nbconvert>=5.1.1',
        'nbformat>=4.3.0',
        'terminaltables',
    ],
    include_package_data=True,
    entry_points='''
    [console_scripts]
    carpo=carpo:cli
    ''',
)
