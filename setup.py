from setuptools import setup

setup(
    name='PyAnime',
    version='0.0.1',
    author='Daniel Hsing',
    description='Download your favourite anime in bulk',
    install_required=[
        'requests',
        'beautifulsoup4',
        'clint',
        'lxml'
    ],
    py_modules=['pyanime'],
    entrypoints={
        'console_scripts': [
            'pyanime=pyanime:main'
        ]
    }
)