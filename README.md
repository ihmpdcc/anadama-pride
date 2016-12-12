# anadama-pride
Framework for submitting proteomics data to the PRIDE archive at EBI 
##Installation
###Requirements
- Python 2.7
- Java x64 (1.8 bit or higher)
- Git
- Setuptools
- Pip
- Aspera ascp client

###Installation Steps
1. Install OSDF-python:
```
pip install 'git+https://github.com/ihmpdcc/osdf-python.git@master#egg=osdf-python-0.3.1'
```
2. Install cutlass:
```
pip install 'git+https://github.com/ihmpdcc/cutlass.git@master#egg=osdf-cutlass-0.8.1'
```
3. Install ANADAMA:
```
pip install 'git+https://bitbucket.org/biobakery/anadama.git@master#egg=anadama-0.0.1'
```
4. Install PRIDE module:
5. Install aspera ascp client:
Download file from `‘http://downloads.asperasoft.com/en/downloads/50’`
Run the installation binary

##Running the pipeline:

1. Update the configuration file ‘.anadama_pride’.
The configuration file is placed in the directory along with pride python code files during installation. 
This file can also be created and placed at User’s home directory(Note: If placed in the home directory, run the pipeline as a that user from command-line) or any directory in python path. While searching for the configuration file, the locations are looked up in the following order:
  - Home directory
  - Code directory
  - Python path

2. Running the pipeline command:

  - Use the basic pipeline command ```‘anadama pipeline run’```
and passing the OSDF id of the study to be submitted when prompted.
  - Pass the OSDF id of the study to be submitted along as a command line argument when starting the pipeline.
```anadama pipeline pride -o ‘collect.study_id:<study-id>’```

3. Help
Help descriptions can be read by the following commnads
```
anadama help pipeline pride
anadama help pipeline
anadama help
```
