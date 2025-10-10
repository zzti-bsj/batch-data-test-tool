#!/usr/bin/env python3
"""
Setup script for batch-data-test-tool
"""

from setuptools import setup, find_packages
import os

# 读取README文件
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

# 读取requirements文件
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

setup(
    name="batch-data-test-tool",
    version="1.0.0",
    author="zzti-bsj",
    author_email="otnw_bsj@163.com",
    description="一个用于批量处理数据并发送HTTP请求的Python工具包",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/zzti-bsj/batch-data-test-tool",
    project_urls={
        "Bug Tracker": "https://github.com/zzti-bsj/batch-data-test-tool/issues",
        "Documentation": "https://github.com/zzti-bsj/batch-data-test-tool#readme",
    },
    packages=find_packages(),
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
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Framework :: Jupyter",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest",
            "pytest-cov",
            "black",
            "flake8",
            "mypy",
        ],
    },
    entry_points={
        "console_scripts": [
            "batch-test-tool=batch_data_test_tool.apps.simple_start:simple_start",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
