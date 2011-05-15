from setuptools import setup

execfile('src/pennypinching/_version.py')
setup(name="pennypinching",
    version=__version__,
    author=__author__,
    author_email='jake.hickenlooper@gmail.com',
    description=__doc__,
    packages=['pennypinching'],
    package_dir={'': 'src'},
    install_requires=[
      'web.py',
      'PyYAML',
      'simplejson', # for python2.5 support
      'pysqlite',
      ],
    include_package_data = True,
    entry_points=("""
      [console_scripts]
      run=pennypinching.site:run
      start=pennypinching.site:start
      stop=pennypinching.site:stop
      """)
    )
