# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='sdamgia-extended-api-extended',
    version='0.1.9',
    author='anijack, CanisLupus25',
    author_email='anijackich@gmail.com',
    description='Python модуль для взаимодействия с образовательным порталом СДАМ ГИА',
    long_description=open('README.md', encoding="utf8").read(),
    long_description_content_type='text/markdown',
    url='https://github.com/CanisLupus25/sdamgia-api-extended',
    license='MIT',
    install_requires=['requests', 'beautifulsoup4', 'pyppeteer', 'grabzit', 'html2image', 'aiohttp'],
    packages = ['sdamgia-extended'],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3'
    ]
)
