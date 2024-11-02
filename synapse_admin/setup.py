from setuptools import setup, find_packages

setup(
    name="synapse-admin",
    version="1.0.0",
    description="Command line tool for Matrix-Synapse administration",
    packages=find_packages(),
    install_requires=[
        "Click>=7.1,<9.0",
        "requests",
        "tabulate",
        "PyYaml",
        "click-option-group>=0.5.2"
    ],
    entry_points="""
        [console_scripts]
        synadmin=synadmin.cli:root
    """,
)
