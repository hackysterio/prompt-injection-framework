from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="promptguard",
    version="1.0.0",
    author="",
    author_email="",
    description="A multi-layered security framework for detecting and mitigating prompt injection attacks in LLM applications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/prompt-injection-framework",
    packages=find_packages(exclude=["tests*", "examples*", "evaluation*"]),
    package_data={
        "promptguard": ["data/*.txt"],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Security",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
)
