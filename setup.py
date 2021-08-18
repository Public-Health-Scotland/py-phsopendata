# Import functions
from setuptools import setup, find_packages

# Setup
setup(
    author="Russell McCreath",
    description="Functions to extract and interact with data from the Scottish Health and Social Care Open Data "
                "platform.",
    name="phsopendata",
    version="0.0.1",
    packages=find_packages(include=["phsopendata", "phsopendata.*"]),
    install_requires=["sys", "requests", "pandas", "io", "pytest"]
)
