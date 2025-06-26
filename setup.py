#!/usr/bin/env python3
"""
Setup configuration for agent_hub package
"""

from setuptools import setup, find_packages
import os

def read_requirements():
    """Read requirements from ai_agents/ai_sdr/requirements.txt"""
    requirements_path = os.path.join("ai_agents", "ai_sdr", "requirements.txt")
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

setup(
    name="agent_hub",
    version="0.1.0",
    description="AI Agents Hub - SDR and other AI agent workflows",
    author="Agent Hub Team",
    python_requires=">=3.11",
    packages=find_packages(),
    include_package_data=True,
    install_requires=read_requirements(),
    entry_points={
        'console_scripts': [
            'sdr-workflow=ai_agents.ai_sdr.sdr.main:main',
            'sdr-orchestrated=ai_agents.ai_sdr.sdr.main_orchestrated:main',
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
    ],
)