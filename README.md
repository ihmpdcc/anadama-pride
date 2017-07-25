# anadama-pride

Framework for submitting proteomics data to the PRIDE archive at EBI 

## Preparation

1. Register with PRIDE website at 'https://www.ebi.ac.uk/pride/archive/'.

2. Contact 'pride-support@ebi.ac.uk' to obtain your FTP credentials.

Visit 'http://www.ebi.ac.uk/pride/help/archive/submission' to get more
information about submitting data to PRIDE.

## Installation

### Requirements

The following system dependencies are required to be installed BEFORE
anadama-pride can be installed and executed:

- Python 2.7
- Java x86_64 (1.8 or higher)
- Git
- Python Setuptools
- Python Pip
- Aspera ascp client

On a Debian or Ubuntu system, the following command will install these
and whatever secondary dependencies they may have:

```
$ sudo apt-get install python2.7 python-pip python-setuptools git openjdk-8-jre-headless
```

### Steps

* Obtain the anadama-pride requirements.txt file

The anadama-pride tool has its own set of Python requirements, which are captured in a
requirements.txt file that lists the python libraries
as dependencies.

```
$ curl -O https://raw.githubusercontent.com/ihmpdcc/anadama-pride/master/requirements.txt
```

This will download the requiements.txt file and place it into your current
working directory.

* Install the software 

Using the 'pip' utility, one can easily install all the dependencies with a
simple command, like so:

```
$ pip install -r requirements.txt 
```

Pip will install the various tools, libraries, and scripts, including
anadama-pride.  When complete, you should see "cutlass", "osdf-python",
"anadama", and "pride" when you execute the following command:

```
$ pip list
```

## Running the pipeline:

1. Update the configuration file ‘.anadama_pride’.

A skeletal configuration file is included with the installation of
anadama-pride and is located in the directory containing the pride python
module. Users have the option of editing this file directly (if they have the
necessary O/S permissions), or they can create an .anadama_pride file in their
home directories.  Another possible location is in the default python search
path, or any directories enumerated in the PYTHONPATH environment variable.
While searching for the configuration file, anadama-pride searches for the
.anadama_pride configuration file in the following locations, in order:

  - Home directory
  - Source code directory
  - Python path (and PYTHONPATH locations)

The .anadama_pride configuration file is in the following format, and needs
values to be appended to each setting:

```
dcc_user=
dcc_pw=
pride_user=
pride_pw=
pride_server=
pride_directory=
submitter_name=
submitter_email=
submitter_affiliation=
lab_head_name=
lab_head_email=
lab_head_affiliation=
submitter_pride_login=
project_title=
project_description=
```

If any of the above settings are left blank (unconfigured), anadama-pride will
error out wih the following message:

```
Please update the configuration file with the required metadata.
```

2. Running the pipeline command:

Users can invoke the pipeline in two ways:

     - Using the basic pipeline command and providing the OSDF id of the study to be submitted interactively when prompted.

```
anadama pipeline run
```

    - Passing the OSDF id of the study to be submitted as a command line argument when starting the pipeline.

```
anadama pipeline pride -o ‘collect.study_id:<study-id>’
```

3. Help

Additional help information can be read by the following commnads

```
anadama help pipeline pride
anadama help pipeline
anadama help
```

## After runnig the pipeline:

Email PRIDE support at 'pride-support@ebi.ac.uk' to notify them about your submission or inquire into
the status of the submission.
