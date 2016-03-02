from setuptools import setup

setup(
    name='PyAnime',
    version='0.0.1',
    author='Daniel Hsing',
    description='Download your favourite anime in bulk',
    install_required=[
        'requests',
        'beautifulsoup4'
    ],
    entrypoints={
        'console_scripts': [
            'sCan=client:main'
        ]
    }
)