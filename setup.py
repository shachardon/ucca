#!/usr/bin/env python

from distutils.core import setup
import os

setup(name='UCCA',
      version='1.0',
      description='Universal Conceptual Cognitive Annotation',
      author='Daniel Hershcovich',
      author_email='danielh@cs.huji.ac.il',
      url='http://www.cs.huji.ac.il/~oabend/ucca.html',
      packages=['ucca', 'scripts'],
      package_dir={
          'ucca': 'ucca',
          'scripts': 'scripts',
          },
      )
