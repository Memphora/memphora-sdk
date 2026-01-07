"""Setup script for Memphora SDK (client-only package)."""
from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent.parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else "Memphora SDK - Persistent memory layer for AI agents"

setup(
    name="memphora",
    version="1.4.0",
    description="Memphora SDK - Persistent memory layer for AI agents (SaaS)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Memphora",
    author_email="info@memphora.ai",
    url="https://memphora.ai",
    project_urls={
        "Homepage": "https://memphora.ai",
        "Documentation": "https://memphora.ai/docs",
        "Source": "https://github.com/Memphora/memphora-sdk",
        "Issues": "https://github.com/Memphora/memphora-sdk/issues",
    },
    packages=find_packages(where="."),
    py_modules=["memphora_sdk", "memory_client"],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.31.0",
        "urllib3>=2.1.0",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    keywords=["ai", "memory", "llm", "vector-database", "embeddings", "semantic-search", "saas"],
)






