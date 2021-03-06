#!/usr/bin/env python
import ez_setup
ez_setup.use_setuptools()

from setuptools import setup

setup(name='GenomeRunner web',
	version='0.1.0',
	author='Mikhail G. Dozmorov, Lukas R. Cara, Cory B. Giles',
	author_email='mikhail.dozmorov@gmail.com, lks_cara@yahoo.com, mail@corygil.es',
	license='License.txt',
	url='http://www.genomerunner.org',
	description='GenomeRunner web: Interpretation of SNP sets within regulatory context',
	long_description=open('README.md').read(),
	packages=['grsnp'],
	package_dir={'grsnp': 'grsnp'},
	include_package_data=True, # Install data from MANIFEST.in
)

