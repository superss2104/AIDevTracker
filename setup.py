from setuptools import setup, find_packages

setup(
    name="aidevtracker",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "openai",
        "python-dotenv",
        "rich",
    ],
    entry_points={
        "console_scripts": [
            "aidt=aidevtracker.main:main",
        ],
    },
    description="Terminal-based AI interaction tracker and code analyzer.",
    python_requires=">=3.8",
)
