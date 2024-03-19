#!/usr/bin/env python

from setuptools import setup, find_packages

readme = open("README.md").read()

setup(
    name="wmmc_bot",
    description="todo",
    author="WMMC",
    author_email="tbd@gmail.com",
    url="https://github.com/KenwoodFox/wmmc-Bot",
    packages=find_packages(include=["wmmc_bot"]),
    package_dir={"wmmc-bot": "wmmc_bot"},
    entry_points={
        "console_scripts": [
            "wmmc-bot=wmmc_bot.__main__:main",
        ],
    },
    python_requires=">=3.10.0",
    version="0.0.0",
    long_description=readme,
    include_package_data=True,
    install_requires=[
        "discord.py",
    ],
    license="MIT",
)
