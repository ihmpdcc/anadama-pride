from setuptools import setup, find_packages
from setuptools.command.install import install

def get_version():
    version_fh = open("CHANGES", "r")
    first_line = version_fh.readline().strip()
    version_fh.close()
    version = first_line.split()[1]
    return version

setup(
    name='pride',
    version=get_version(),
    description="Framework for submitting proteomics data to the PRIDE archive at EBI",
    packages=["pride"],
    zip_safe=False,
    install_requires=[
        'anadama',
        'osdf-python',
        'cutlass'
    ],
    package_data={'': ['.anadama_pride','pg-converter-1.2/*.*','pg-converter-1.2/lib/*.*']},
    include_package_data=True,
    entry_points= {
        'anadama.pipeline': [
            ".pride = pride.pipeline:PRIDEPipeline"
        ]
    }
)
