"""Continuous Face Zero Trust - Python SDK Package."""

from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="continuous-face-zero-trust",
    version="1.0.0",
    description="Continuous Face Zero Trust Authentication SDK",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cfzt/continuous-face-zero-trust",
    author="CFZT Team",
    author_email="team@cfzt.io",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Security :: Cryptography",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    keywords="zero-trust face-recognition post-quantum-cryptography quantum-resistant authentication",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.10",
    install_requires=[
        "cryptography>=41.0.0",
        "pydantic>=2.0.0",
        "httpx>=0.25.0",
        "numpy>=1.24.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "ruff>=0.1.0",
            "mypy>=1.5.0",
        ],
        "ml": [
            "onnxruntime>=1.15.0",
            "pillow>=10.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "cfzt=cfzt.cli:main",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/cfzt/continuous-face-zero-trust/issues",
        "Source": "https://github.com/cfzt/continuous-face-zero-trust",
    },
)
