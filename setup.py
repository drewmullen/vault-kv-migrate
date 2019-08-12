# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from distutils.core import Command


class DisabledCommands(Command):
    user_options = []

    def initialize_options(self):
        raise Exception('This command is disabled')

    def finalize_options(self):
        raise Exception('This command is disabled')


with open('README.md') as f:
    readme = f.read()

requirements = [
    'hvac==0.9.5'
]

# Version here doesnt matter much since we are not
# installing this outside of our repo or shipping
# to pypi
setup(
    version='0.1.0',
    name='vault-kv-migrate',
    description='Sample package for Python-Guide.org',
    long_description=readme,
    author='Drew Mullen',
    author_email='mullen.drew@gmail.com',
    url='https://github.com/drewmullen/vault-kv-migrate',
    packages=find_packages(exclude=('tests', 'docs')),
    install_requires=requirements,
    cmdclass={'register': DisabledCommands,
              'upload': DisabledCommands}
)
