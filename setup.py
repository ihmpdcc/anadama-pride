from setuptools import setup, find_packages
from setuptools.command.install import install
		
setup(
    name='pride',
    version='0.0.1',
    description="Transfer sequence files and metadata from the iHMP DCC to PRIDE repository",
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
