#!/usr/bin/env python

from distutils.core import setup
import os

setup(name='UCCA',
      version='1.0',
      description='Universal Conceptual Cognitive Annotation',
      author='Daniel Hershcovich',
      author_email='danielh@cs.huji.ac.il',
      url='http://www.cs.huji.ac.il/~oabend/ucca.html',
      packages=['ucca', 'scenes', 'scripts', 'parsing',
          'classifiers', 'features', 'state'],
      package_dir={
          'ucca': 'ucca',
          'scenes': 'scenes',
          'scripts': 'scripts',
          'parsing': 'parsing',
          'classifiers': os.path.join('parsing', 'classifiers'),
          'features': os.path.join('parsing', 'features'),
          'state': os.path.join('parsing', 'state'),
          },
      )
