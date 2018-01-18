# -*- coding: utf-8 -*-
from setuptools import setup

scripts = ['bin/borgcron']
packages = ['borgcron']
data_files = [('/etc/borgcron/', ['etc/cfg_example.yml'])]
install_requires = ['PyYAML']
tests_require = ['nose']

setup(name = 'borgcron',
      version = '0.2',
      description = 'execute borgbackup without user interaction',
      url = '',
      author = 'Thomas Kärgel',
      author_email = 'kaergel at b1-systems.de',
      license = 'MIT',
      scripts = scripts,
      packages = packages,
      data_files = data_files,
      install_requires = install_requires,
      zip_safe = False,
      test_suite = 'nose.collector',
      tests_require = tests_require)
