#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.md') as readme_file:
    readme = readme_file.read()

# with open('HISTORY.md') as history_file:
#     history = history_file.read()

requirements = [ 'pandas', 'spacy', 'elasticsearch', 'beautifulsoup4', 'vaderSentiment', 'docker', ]

setup_requirements = ['pytest-runner', 'twine', ]

test_requirements = ['pytest', 'scikit-learn', ]

setup(
    author="Philipp Thomann",
    author_email='philipp.thomann@d-one.ai',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        # "Programming Language :: Python :: 2",
        # 'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        # 'Programming Language :: Python :: 3.4',
        # 'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Text Processing :: Markup :: HTML',
    ],
    description="Easy Peasy Language Squeezy",
    install_requires=requirements,
    license="Apache Software License 2.0",
    long_description=readme + '\n\n', # + history,
    long_description_content_type='text/markdown',
    include_package_data=True,
    keywords='nlpeasy',
    name='nlpeasy',
    packages=find_packages(include=['nlpeasy']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/d-one/nlpeasy',
    version='0.6.2',
    zip_safe=False,
)
