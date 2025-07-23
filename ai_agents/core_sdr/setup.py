#!/usr/bin/env python3
"""
Setup script for the Lead Generation System
"""

from pathlib import Path

from setuptools import setup, find_packages

# Read README for long description
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Dependencies are now defined in pyproject.toml
# This setup.py is kept for backward compatibility only
requirements = [
    "requests>=2.28.0",
    "fastapi>=0.104.0",
    "uvicorn>=0.24.0",
    "pydantic>=2.0.0",
    "click>=8.1.0",
    "python-dotenv>=1.0.0",
    "pymongo>=4.5.0",
    "pandas>=2.0.0",
    "python-dateutil>=2.8.0",
    "httpx>=0.25.0"
]

setup(
    name="core-sdr-leadgen",
    version="1.0.0",
    description="A sophisticated lead generation system using natural language queries",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Lead Generation Team",
    author_email="team@example.com",
    url="https://github.com/example/core-sdr",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "core_sdr": [
            "config/*.json",
            "data/.gitkeep",
            "logs/.gitkeep"
        ]
    },
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0"
        ]
    },
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "leadgen=core_sdr.__main__:main",
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="lead generation, company search, natural language processing, coresignal",
    project_urls={
        "Bug Reports": "https://github.com/example/core-sdr/issues",
        "Source": "https://github.com/example/core-sdr",
        "Documentation": "https://github.com/example/core-sdr/blob/main/README.md",
    }
)