from setuptools import setup, find_packages

setup(
    name="ai-bos-core",
    version="1.0.0",
    description="AI Biological Operating System — Open Source Core",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="AMPM Labs",
    author_email="chainuncel0712@gmail.com",
    url="https://github.com/chainuncel0712/AMPM-AI-BOS",
    packages=find_packages(),
    python_requires=">=3.10",
    license="AGPL-3.0 + Additional Restrictions",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
    ],
)
