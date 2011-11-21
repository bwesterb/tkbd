#!/usr/bin/env python
# vim: et:sta:bs=2:sw=4:

from setuptools import setup, find_packages
from get_git_version import get_git_version

setup(name='tkbd',
    version=get_git_version(),
    description='Terminal Kamer Bezetting Daemon voor de faculteit NWI '+
                    'van de Radboud Universiteit',
    author='Bas Westerbaan',
    author_email='bas@westerbaan.name',
    url='http://github.com/bwesterb/tkbd',
    packages=['tkbd'],
    package_data={'': ['*.mirte']},
    zip_safe=False,
    package_dir={'tkbd': 'src'},
    install_requires = [
            'docutils>=0.3',
            'mirte>=0.1.0a2',
            'sarah>=0.1.0a2',
            'joyce>=0.1.0a2'],
    )