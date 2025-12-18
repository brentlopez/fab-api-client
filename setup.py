"""Setup script for fab-api-client."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

setup(
    name="fab-api-client",
    version="0.1.0",
    author="Brent Lopez",
    description="Python client library for Epic Games Fab API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/fab-api-client",
    packages=find_packages(exclude=["tests", "cli", "scripts"]),
    package_data={
        "fab_api_client": ["schemas/*.json"],
    },
    install_requires=[
        "requests>=2.31.0",
    ],
    extras_require={
        "validation": ["jsonschema>=4.0.0"],
        "cli": ["tqdm>=4.66.0"],
        "dev": [
            "jsonschema>=4.0.0",
            "tqdm>=4.66.0",
            "pytest>=7.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "fab-manifest-downloader=cli.main:main",
        ],
    },
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
