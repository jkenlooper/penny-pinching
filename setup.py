from setuptools import setup, find_packages
import os

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

execfile('src/pennypinching/_version.py')
setup(name="pennypinching",
    version=__version__,
    author=__author__,
    author_email='jake@weboftomorrow.com',
    description=__doc__,
    long_description=read('README.md'),
    packages=find_packages('src'),
    package_dir={'': 'src'},
    install_requires=[
      'setuptools',
      'web.py',
      'PyYAML',
      'simplejson', # for python2.5 support
      'pysqlite',
      ],
    include_package_data = True,
    entry_points={
      'console_scripts': [
        'pennypinching = pennypinching.site:main'
       ]
    }
)
