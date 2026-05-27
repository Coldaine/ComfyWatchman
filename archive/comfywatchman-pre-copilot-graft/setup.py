"""
Setup script for ComfyFixerSmart

This setup.py is provided for backward compatibility with older pip versions
and build systems that don't yet support pyproject.toml fully.

For modern Python packaging, see pyproject.toml.
"""

from setuptools import setup

# Read version from package
def get_version():
    """Get version from package __init__.py"""
    with open("src/comfywatchman/__init__.py", "r") as f:
        for line in f:
            if line.startswith("__version__"):
                return line.split("=")[1].strip().strip('"')
    raise RuntimeError("Unable to find version string.")

# Read README
def get_long_description():
    """Get long description from README.md"""
    try:
        with open("README.md", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "ComfyWatchman - ComfyUI workflow readiness and model management"

setup(
    name="comfywatchman",
    version=get_version(),
    description="Incremental ComfyUI model downloader with intelligent search and verification",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="ComfyWatchman Team",
    author_email="comfywatchman@example.com",
    url="https://github.com/yourusername/comfywatchman",
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Utilities",
    ],
    keywords="comfyui stable-diffusion model-downloader automation ai",
    python_requires=">=3.7",
    package_dir={"": "src"},
    packages=["comfywatchman"],
    include_package_data=True,
    install_requires=[
        "requests>=2.25.0",
        "tomli>=1.2.0; python_version < '3.11'",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
            "sphinx>=4.0.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
        "docs": [
            "sphinx>=4.0.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "comfywatchman=comfywatchman.cli:main",
        ],
    },
    project_urls={
        "Homepage": "https://github.com/yourusername/comfywatchman",
        "Documentation": "https://comfywatchman.readthedocs.io/",
        "Repository": "https://github.com/yourusername/comfywatchman.git",
        "Issues": "https://github.com/yourusername/comfywatchman/issues",
        "Changelog": "https://github.com/yourusername/comfywatchman/blob/main/CHANGELOG.md",
    },
)
