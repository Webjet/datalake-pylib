# ========================= #
# POSTGRES SETUP            #
# ========================= #

from setuptools import setup, find_namespace_packages
import os

# ========================= #
# METHODS                   #
# ========================= #

def read(rel_path: str) -> str:
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, rel_path)) as fp:
        return fp.read()

def get_version(rel_path: str) -> str:
    for line in read(rel_path).splitlines():
        if line.startswith("__version__"):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    raise RuntimeError("Unable to find version string.")

# ========================= #
# SETUP                     #
# ========================= #

long_description = read('README.md')

setup(
    name="datalake-sdk",
	version=get_version("src/datalake/sdk/__init__.py"),
	description="Database library to work with DataFrames with Postgres and Athena.",
	long_description=long_description,
	classifiers=[
		"Intended Audience :: Developers",
		"License :: OSI Approved :: MIT License",
		"Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
	],
	url="https://github.com/Webjet/datalake-pylib",
	author="Carlos Pomares",
	author_email="carlos.pomares@webbeds.com",
	package_dir={"": "src"},
	packages=find_namespace_packages(
		where="src",
		exclude=["test","scripts"],
	),
	python_requires=">=3.7",
    install_requires=[
		"requests >= 2.22.0",
		"datalake-etl-schema @ git+ssh://github.com/Webjet/datalake-pylib#egg=datalake-etl-schema&subdirectory=etl/schema"
	],
)