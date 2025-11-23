#!/usr/bin/env python3
"""
Setup script for Nogger - A Better Logger
"""

from setuptools import setup, find_packages
from setuptools.command.install import install
from pathlib import Path
import sys
import os


class PostInstallCommand(install):
    """Post-installation hook to create default config file"""
    
    def run(self):
        # Run the standard installation
        install.run(self)
        
        # Post-install message
        print(f"\n✓ Nogger installed successfully!")
        print(f"  Run 'nogger-config' in your project directory to create a config file.")
        print(f"  Or use: python -m nogger_package._config")


# Read README for long description
readme_file = Path(__file__).parent / "README.md"
if readme_file.exists():
    with open(readme_file, "r", encoding="utf-8") as fh:
        long_description = fh.read()
else:
    long_description = "Nogger - A Better Logger with British English and async support"


setup(
    name="nogger",
    version="1.0.0",
    author="Nogger Development Team",
    author_email="",
    description="A comprehensive, async-friendly logging library with British English",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Logging",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    keywords="logging logger async british english colours yaml configuration",
    python_requires=">=3.8",
    install_requires=[
        "pyyaml>=6.0.1",
    ],
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-asyncio>=0.21.0',
        ],
    },
    cmdclass={
        'install': PostInstallCommand,
    },
    entry_points={
        'console_scripts': [
            'nogger-config=nogger_package._config:cli_create_config',
        ],
    },
    package_data={
        'nogger_package': ['*.yaml', '*.yml'],
    },
    include_package_data=True,
    zip_safe=False,
)
