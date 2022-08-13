import setuptools
from distutils.core import setup

setuptools.setup(
    name='imeonm',
    version='0.1',
    author='Jean-Baptiste BESNARD',
    description='This is the companion plotting program for iocrawl.',
    entry_points = {
        'console_scripts': ['imeonm=imeonm.cli:run'],
    },
    packages=["imeonm"],
    install_requires=[
        'matplotlib',
        "prometheus-client",
        'wheel'
    ],
    python_requires='>=3.5'
)
