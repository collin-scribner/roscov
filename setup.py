import os
import sys
from setuptools import setup, find_packages
from roscov.src import __version__

exec(open(os.path.join(os.path.dirname(__file__), 'src', 'roscov', '__init__.py')).read())

setup(
    name='roscov',
    version=__version__,
    install_requires=['setuptools'],
    python_requires='>3.5.2',
    package_dir={'': 'src'},
    packages=find_packages(),
    entry_points = {
        'console_scripts': [
            'roscov=roscov.cli:main'
        ],
    },
    author='Collin Scribner',
    author_email='collinscribner13@gmail.com',
    maintainer='Collin Scribner',
    maintainer_email='collinscribner13@gmail.com',
    url='https://github.com/collin-scribner/roscov',
    keywords=['ROS', 'coverage', 'code coverage'],
    classifiers=['Programming Language :: Python',],
    description="",
    long_description="""A tool for obtaining code coverage statistics for a ROS-based workspace, repository, or package.
    Used in conjunction with lcov for obtaining C++ coverage and is based off of Mike Ferguson's code_coverage package on GitHub.
    """,
    license='BSD'
)
