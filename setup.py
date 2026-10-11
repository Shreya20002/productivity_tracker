"""
Setup script for Screen Time & App Usage Tracker
"""

from setuptools import setup, find_packages
import os

# Read the README file
readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
long_description = ""
if os.path.exists(readme_path):
    with open(readme_path, 'r', encoding='utf-8') as f:
        long_description = f.read()

setup(
    name="screen-time-tracker",
    version="1.0.0",
    author="Screen Time Tracker",
    author_email="",
    description="A simple terminal application to track application usage time",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/screen-time-tracker",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Utilities",
        "Topic :: System :: Monitoring",
    ],
    python_requires=">=3.6",
    install_requires=[
        # No external dependencies - uses only Python standard library
    ],
    entry_points={
        "console_scripts": [
            "screen-time-tracker=screen_time_tracker.__main__:main",
            "stt=screen_time_tracker.__main__:main",
        ],
    },
    include_package_data=True,
    package_data={
        "screen_time_tracker": ["data/.gitkeep"],
    },
    keywords="screen time, app usage, tracker, productivity, monitoring",
)
