'''
Created on Mar 9, 2014

@author: Anduril
'''
from setuptools import setup, find_packages

setup(
        name = "ChorusCore",
        version = "0.9.002",
        description = "A test framework based on unittest, support baselines assertion, give pretty html report",
        author = "Anduril, mxu",
        author_email = "yjckralunr@gmail.com",
        packages = ['ChorusCore'],
        zip_safe = False,
        include_package_data = True,
        install_requires = [
                                'httplib2>=0.8',
                                'Jinja2>=2.6',
                                'mysql-connector-python>=1.0.10',
                                'PIL>=1.1.7',
                                'python-Levenshtein>=0.10.2'
                            ],
        url = "https://github.com/ChorusCore/"
      )
