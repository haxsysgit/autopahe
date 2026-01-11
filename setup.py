#!/usr/bin/env python3
"""
AutoPahe Setup Script for PyPI Distribution
"""

from setuptools import setup, find_packages
import os

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
def read_requirements():
    requirements = []
    if os.path.exists("requirements.txt"):
        with open("requirements.txt", "r", encoding="utf-8") as f:
            requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return requirements

setup(
    name="autopahe",
    version="3.4.4",
    author="haxsys",
    author_email="haxsysgit@gmail.com",
    description="Download and stream anime episodes easily from AnimePahe",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/haxsysgit/autopahe",
    project_urls={
        "Bug Tracker": "https://github.com/haxsysgit/autopahe/issues",
        "Documentation": "https://github.com/haxsysgit/autopahe/blob/main/README.md",
        "Source Code": "https://github.com/haxsysgit/autopahe",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Video",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Natural Language :: English",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.25.0",
        "beautifulsoup4>=4.9.0",
        "colorama>=0.4.4",
        "tqdm>=4.60.0",
        "playwright>=1.45.0",
        "rich>=13.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "black>=21.0",
            "flake8>=3.8",
            "build>=0.3.0",
            "twine>=3.4.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "autopahe=auto_pahe:main",
            "auto-pahe=auto_pahe:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.yml", "*.yaml"],
    },
    keywords=[
        "anime",
        "download", 
        "stream",
        "animepahe",
        "command-line",
        "cli",
        "video",
        "episodes",
        "media",
    ],
    zip_safe=False,
)
