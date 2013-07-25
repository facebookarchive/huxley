from setuptools import setup, find_packages
import os

DIRNAME = os.path.dirname(os.path.abspath(__file__))

setup(
    name = 'Huxley',
    version = '0.1',
    packages = find_packages(),
    install_requires = open(os.path.join(DIRNAME, 'requirements.txt'), 'r').readlines(),
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
