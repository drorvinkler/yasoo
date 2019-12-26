import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="yasoo",
    version="0.1.2",
    author="Dror A. Vinkler",
    description="Yet another serializer of objects",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/drorvinkler/yasoo",
    packages=['yasoo'],
    install_requires=[
        'attrs>=16.2',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
