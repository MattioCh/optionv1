from setuptools import setup, find_packages

setup(
    name="optionv1",
    description="A Python package for option data analysis",
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=["pandas>=1.3.0", "numpy>=1.21.0", "yfinance", "ipykernel"],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "black",
            "flake8",
        ],
    },
    package_data={
        "horse": [],
    },
    include_package_data=True,
)
