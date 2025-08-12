#!/usr/bin/env python3
"""
Setup configuration for agent_hub package
"""

from setuptools import setup, find_packages
import os


def read_requirements():
    """Read requirements from root requirements.txt"""
    requirements_path = "requirements.in"
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r') as f:
            return [line.strip() for line in f
                    if line.strip() and not line.startswith('#') and not line.startswith('# ')]
    return []


setup(
    name="agent_hub",
    version="0.1.0",
    description="AI Agents Hub - SDR and other AI agent workflows including Core SDR lead generation",
    author="Agent Hub Team",
    python_requires=">=3.8",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "ai_agents.core_sdr": [
            "src/prompts/*.txt",
            "src/config/*.json",
            "src/data/.gitkeep",
            "src/logs/.gitkeep"
        ]
    },
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0"
        ]
    },
    entry_points={
        'console_scripts': [
            'sdr-workflow=ai_agents.ai_sdr.sdr.main:main',
            'sdr-orchestrated=ai_agents.ai_sdr.sdr.main_orchestrated:main',
            'leadgen=ai_agents.leadgen.cli:cli',
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="ai agents, sdr, lead generation, company search, natural language processing",
    project_urls={
        "Bug Reports": "https://github.com/example/agent_hub/issues",
        "Source": "https://github.com/example/agent_hub",
    }
)
