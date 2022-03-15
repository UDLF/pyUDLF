from setuptools import setup, find_packages
from setuptools.command.install import install
import os
import subprocess


with open('PKG-INFO', 'r') as f:
    long_description = f.read()


def install_requirements():
    print('Installing pyUDLF requirements...')
    subprocess.call('pip install -r requirements.txt',
                    shell=True)


class InstallClass(install):
    def run(self):
        install_requirements()
        install.run(self)


setup(
    name='pyUDLF',
    version='0.8',
    description='Python wrapper for UDLF',
    license='GPLv2',
    long_description=long_description,
    author='UNESP',
    python_requires='>=3.6',
    packages=find_packages(),
    zip_safe=False,
    cmdclass={'install': InstallClass}
)
