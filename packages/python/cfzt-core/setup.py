from setuptools import setup, find_packages

setup(
    name="cfzt-core",
    version="0.1.0",
    author="quantumworld-dpdns-io",
    description="Shared library for Continuous Face Zero Trust",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.12",
    install_requires=[
        "pydantic>=2.7.1",
        "cryptography>=42.0.0",
        "python-jose[cryptography]>=3.3.0",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.12",
        "Topic :: Security :: Cryptography",
    ],
)
