#!/usr/bin/env python
# vim: et:sta:bs=2:sw=4:

from setuptools import setup, find_packages, findall
from get_git_version import get_git_version
import os, os.path

def find_package_data():
    base = os.path.join(os.path.dirname(__file__), 'src')
    s, r = ['.'], []
    while s:
        p = s.pop()
        for c in os.listdir(os.path.join(base, p)):
            if os.path.isdir(os.path.join(base, p, c)):
                s.append(os.path.join(p, c))
            elif c.endswith('.mirte'):
                r.append(os.path.join(p, c))
    return r

setup(name='tkbd',
    version=get_git_version(),
    description='Terminal Kamer Bezetting Daemon voor de faculteit NWI '+
                    'van de Radboud Universiteit',
    author='Bas Westerbaan',
    author_email='bas@westerbaan.name',
    url='http://github.com/bwesterb/tkbd',
    packages=['tkbd'],
    zip_safe=False,
    package_dir={'tkbd': 'src'},
    package_data={'tkbd': find_package_data()},
    install_requires = [
            'docutils>=0.3',
            'mirte>=0.1.0a3',
            'sarah>=0.1.2',
            'msgpack-python>=0.1.10',
            'joyce>=0.1.2'],
    )
