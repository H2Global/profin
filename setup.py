# -*- coding: utf-8 -*-
"""
Created on Sat Oct 14 12:19:05 2023

@author: j.reul
"""

from setuptools import setup

setup(name='profin',
      version='1.7',
      description='Monte-carlo simulation of energy-project KPIs',
      author='Julian Reul',
      author_email='julian.reul@rwth-aachen.de',
      license='MIT',
      packages=['profin'],
      include_package_data=True,
      zip_safe=False)