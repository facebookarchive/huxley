from setuptools import setup, find_packages
import os

DIRNAME = os.path.dirname(os.path.abspath(__file__))

execfile(os.path.join(DIRNAME, 'huxley', 'version.py'))

setup(
    name = 'Huxley',
    version = __version__,
    packages = find_packages(),
    install_requires = [
        'selenium==2.35.0',
        'plac==0.9.1',
        'Pillow==2.2.1',
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
