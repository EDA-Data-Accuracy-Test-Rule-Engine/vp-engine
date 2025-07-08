from setuptools import setup, find_packages

setup(
    name="vp-engine",
    version="1.0.0",
    description="VP Data Accuracy Test Rule Engine - Interactive data validation platform with AI-powered rule suggestions",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="VP Bank Technology Team",
    author_email="tech@vpbank.com.vn",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        line.strip() 
        for line in open("requirements.txt").readlines() 
        if line.strip() and not line.startswith("#")
    ],
    entry_points={
        "console_scripts": [
            "vp-engine=src.cli.main:cli",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Database :: Database Engines/Servers",
        "Topic :: Software Development :: Quality Assurance",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)