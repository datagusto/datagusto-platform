from setuptools import setup, find_packages

# Read README file for long description
try:
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()
except FileNotFoundError:
    long_description = (
        "Datagusto SDK for Python - A data quality guardrail SDK for AI agents"
    )

setup(
    name="datagusto-sdk",
    version="0.1.5",
    author="Datagusto",
    author_email="support@datagusto.jp",
    description="A data quality guardrail SDK for AI agents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/datagusto/datagusto-platform",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "langchain-core>=0.1.0",
        "requests>=2.25.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.910",
        ],
    },
    keywords="ai, data quality, guardrails, data governance",
    project_urls={
        "Bug Reports": "https://github.com/datagusto/datagusto-platform/issues",
        "Source": "https://github.com/datagusto/datagusto-platform",
    },
    include_package_data=True,
    zip_safe=False,
)
