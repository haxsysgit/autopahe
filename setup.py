from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name = 'autopahe',
    version = '2.3.2',
    author_email="pentacker@gmail.com",
    description = "A python script to automate downloads from animepahe",
    url = "https://github.com/haxsysgit/autopahe",
    author = "Elenasulu Arinze",
    license = "MIT",
    py_modules = [
        'autopahe',

    ],
    package_dir = {'autopahe':'autopahe'},
    entry_points ={
            'console_scripts': ['autopahe = autopahe.auto_pahe:main']
    },
    include_package_data=True,
    packages = [
        "autopahe",
    ],
    python_requires = '>=3.7',
    install_requires = [
        'beautifulsoup4 >= 4.9.3',
        'selenium >= 3.141.0',
        'requests >= 2.25.1',
        'webdriver-manager >= 3.8.5',
        'tqdm >= 4.61.0',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',  
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Operating System :: Microsoft :: Windows :: Windows 10",
        "Operating System :: POSIX :: Linux",
    ],

    long_description = long_description,
    long_description_content_type = "text/markdown",

)