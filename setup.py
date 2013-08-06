import huxley
from setuptools import setup, find_packages
import os

DIRNAME = os.path.dirname(os.path.abspath(__file__))

setup(
    name = 'Huxley',
    version = huxley.__version__,
    packages = find_packages(),
    install_requires = [
        'selenium==2.32.0',
        'plac==0.9.1',
        'PIL==1.1.7',
        'jsonpickle==0.4.0'
    ],
    package_data={'': ['requirements.txt']},
    entry_points = {
        'console_scripts': [
            'huxley=huxley.cmdline:main'
        ]
    },
    author = 'Pete Hunt',
    author_email = 'pete.hunt@fb.com',
    description = 'Watches you browse, takes screenshots, tells you when they change.',
    license = 'Apache 2',
    keywords = 'selenium testing facebook instagram',
    url = 'http://github.com/facebook/huxley',
)
