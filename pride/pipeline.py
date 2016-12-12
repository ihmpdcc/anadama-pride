import os
import inspect
import getpass
import subprocess
import sys
import re
import shutil

import cutlass
import anadama.pipelines

from collections import OrderedDict
from . import workflows
from . import PrepProt

def get_proteomes(preps):
	def _ps():
		for prep in preps:
			proteome_list=list()
			for proteome in prep.proteomes():
				proteome_list.append(proteome)
			if len(proteome_list)!= 0:
				yield prep, proteome_list
	return map(PrepProt._make, _ps())

# Utility function to check whether the required softwares are installed.
def check_software_dependencies():
	print('checking software dependencies')
	# Check if ASCP is installed
	try:
		return_status=subprocess.check_output(["ascp", "-A"])
	except OSError as e:
		print('ASCP not installed or configured. Please install/configure ASCP.')
		sys.exit(1)
	# Check if Java(x64) greater than version 1.8 is intalled
	try:
		return_status=subprocess.check_output(["java", "-d64", "-version"], stderr=subprocess.STDOUT)
	except subprocess.CalledProcessError as e:
		print('64-bit Java not installed. Please install 64-bit java.')
		sys.exit(1)
	version=re.findall('"([^"]*)"',return_status.splitlines()[0])[0]
	if version<'1.8':
		print("Java verson 1.8 or greater required.")
		sys.exit(1)


class PRIDEPipeline(anadama.pipelines.Pipeline):
	""" Pipeline for submitting proteomics data from iHMP DCC's OSDF instance
	to PRIDE repository.

	Steps:
	1. Given an OSDF id number for a Study, query the database to retrieve all the proteome
	instances included in the study.

	2. For each proteome instance retrieved, download the rsult file (in .mzid format) along
	with the related peak file (in .mgf format), raw data file(s) and other files(if present).

	3. Validate each set of result and related peak files using PRIDE Converter tool.

	5. Create a submission summary file (submission.px) required for submitting the data.

	6. Submit the entire set of files along with the submission file created in the previos
	step to the PRIDE respository
	"""
	name="PRIDE"

	default_options = {
		"collect": {
			"dcc_user": None,
			"dcc_pw": None,
			"study_id": None,
		},
		"submit": {
			"pride_user": None,
			"pride_pw": None,
			"pride_server": None,
			"pride_directory": None,
		}
	}

	workflows= {
		"collect": workflows.collect,
		"submit": workflows.submit,
	}

	project_metadata = OrderedDict([                 # Field populated from
		("submitter_name", None),                 # .anadama_pride config file
		("submitter_email", None),                # .anadama_pride config file
		("submitter_affiliation", None),          # .anadama_pride config file
		("lab_head_name", None),                  # .anadama_pride config file
		("lab_head_email", None),                 # .anadama_pride config file
		("lab_head_affiliation", None),           # .anadama_pride config file
		("submitter_pride_login", None),          # .anadama_pride config file
		("project_title", None),                  # .anadama_pride config file
		("project_description", None),            # .anadama_pride config file
		("sample_processing_protocol", None),     # Field 'protocol_steps' from
												  # corresponding assey_prep
		("data_processing_protocol", None),       # Field 'data_processing_protocol' from
												  # corresponding prodeome
		("keywords", ''),                         # Field 'species' from
												  # corresponding assey_prep
		("submission_type", 'COMPLETE'),          # Only 'Complete' submissions are done
											      # Thats the way of a 'Shinobi'.
		("experiment_type", list()),              # Field 'experiment_type' from
												  # corresponding assey_prep
		("species", list()),                      # Field 'species' from
												  # corresponding assey_prep
		("tissue", list()),                       # Field 'tissue' from
												  # corresponding assey_prep
		("instrument", list()),                   # Field 'instrument_name' from
												  # proteome OSDF entry
	])


	def __init__(self, workflow_options=dict(), *args, **kwargs):
		""""""
		super(PRIDEPipeline, self).__init__(*args, **kwargs)

		check_software_dependencies()
		config_file=None

		# Check if config file is present in the following places in order of precedence:
		# 1. User's Home directory
		# 2. The directory where the module code is present
		# 3. Any directory included in python path variable
		path=os.path.expanduser("~")
		file_path=os.path.join(path,'.anadama_pride')
		if config_file is None and os.path.exists(file_path):
			config_file=file_path

		path=os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
		file_path=os.path.join(path,'.anadama_pride')
		if config_file is None and os.path.exists(file_path):
			config_file=file_path

		paths=sys.path
		for path in paths:
			file_path=os.path.join(path,'.anadama_pride')
			if config_file is None and os.path.exists(file_path):
				config_file=file_path

		if config_file is None:
			print('Config file not present.')
			sys.exit(1)

		self.options = self.default_options.copy()
		# Update the options to user provided options
		for k in self.options.iterkeys():
			self.options[k].update(workflow_options.get(k, {}))

		# Read the .anadama_pride config file
		with open(config_file) as _file:
			for line in _file.readlines():
				tags=line.strip('\n').split('=')
				#Update the DCC Username and Password Fields
				if(tags[0]=='dcc_user' or tags[0]=='dcc_pw'):
					if len(tags[1]) == 0:
						print('Please update the configuration file with your DCC username and password.')
						sys.exit(1)
					self.options['collect'][tags[0]] = tags[1]
				# Update PRIDE username, password and server fields
				elif(tags[0]=='pride_user' or tags[0]=='pride_pw' or tags[0]=='pride_server' or tags[0]=='pride_directory'):
					# print tags[0]
					if len(tags[1]) ==0:
						print('Please update the configuration file with your PRIDE credentials.')
						sys.exit(1)
					self.options['submit'][tags[0]] = tags[1]
				#Update the project metadata fileds
				else:
					if len(tags[1]) == 0:
						print('Please update the configuration file with the required metadata.')
						sys.exit(1)
					self.project_metadata[tags[0]] = tags[1]
				if(tags[0]=='project_description' and (len(tags[1])<50 or len(tags[1])>500)):
					print('The length of the Project Description field must be between 50 to 500 charachters.')
					sys.exit(1)
		_file.close()
		if not self.options['collect'].get('study_id', None):
			prompt="Enter the study ID to submit: "
			self.options['collect']['study_id'] = raw_input(prompt)


	def metadata_from_prep(self,prepprot):
		assay_prep = prepprot.prep

		# There might be multiple proteome and multiple assay_preps included in one submission.
		# The assumption made here is that the protocol stpes remains the same for all the
		# assay_preps that belong to the study being submitted. Therefore, the metadata field
		# 'sample_processing_protocol' is populated only from the first assay prep encountered.

		if(self.project_metadata["sample_processing_protocol"] is None):
			spp_string=assay_prep._protocol_steps
			if (len(spp_string) < 50 or len(spp_string) > 500):
				print('The length of the Sample Processing Protocol field must be between 50 to 500 charachters.\n'
				      'Please update the field protocol_steps in the related assay_prep entry in OSDF.')
				sys.exit(1)
			self.project_metadata["sample_processing_protocol"] = spp_string

		if assay_prep._experiment_type not in self.project_metadata["experiment_type"]:
			self.project_metadata["experiment_type"].append(assay_prep._experiment_type)

		if assay_prep._species not in self.project_metadata["keywords"]:
			self.project_metadata["keywords"] = self.project_metadata["keywords"] + assay_prep._species

		if assay_prep._species not in self.project_metadata["species"]:
			self.project_metadata["species"].append(assay_prep._species)

		if assay_prep._tissue not in self.project_metadata["tissue"]:
			self.project_metadata["tissue"].append(assay_prep._tissue)

		for proteome in prepprot.proteome:
			if proteome._instrument_name not in self.project_metadata["instrument"]:
				self.project_metadata["instrument"].append(proteome._instrument_name)

			# There might be multiple proteomes included in one submission.
			# The assumption made here is that the data processing protocol remains the same for all the
			# proteomes that belong to the study being submitted. Therefore, the metadata field
			# 'data_processing_protocol' is populated only from the first proteome encountered.

			if (self.project_metadata["data_processing_protocol"] is None):
				dpp_string = proteome._data_processing_protocol
				if (len(dpp_string) < 50 or len(dpp_string) > 500):
					print('The length of the Data Processing Protocol field must be between 50 to 500 charachters.\n'
					      'Please update the field data_processing_protocol in the related proteome entry in OSDF.')
					sys.exit(1)
				self.project_metadata["data_processing_protocol"] = dpp_string




	def _configure(self):

		session = cutlass.iHMPSession(self.options['collect']['dcc_user'],
									  self.options['collect']['dcc_pw'])

		# Connect to OSDF with the provided username and pasword
		try:
			session._osdf.get_info()
		except ValueError as e:
			print('Cannot connect to OSDF. Please check OSDF Username and Password')
			sys.exit(1)

		# Retrive the study instance for the id number provided.
		try:
			study = cutlass.Study.load(self.options['collect']['study_id'])
		except Exception as e:
			print('No study found with the entered study ID')
			sys.exit(1)

		# The name of folder containg the data to be submitted is the OSDF id of study being submitted.
		result_dir=os.path.join(os.getcwd(),self.options['collect']['study_id'])

		if os.path.exists(result_dir):
			print('Removing existing result folder')
			shutil.rmtree(result_dir)
		os.mkdir(result_dir, 0777)

		# Retrieve each proteome derived from either a host assay prep or a micrebiome assay prep
		# prepared form each sample collected during each visit by each subject that participated
		# in the given study.
		record_proteomes=list()
		for subject in study.subjects():
			for visit in subject.visits():
				for sample in visit.samples():
					host_assay_preps=get_proteomes(sample.hostAssayPreps())
					if host_assay_preps:
						record_proteomes.append(host_assay_preps)
					micro_assay_preps=get_proteomes(sample.microbAssayPreps())
					if micro_assay_preps:
						record_proteomes.append(micro_assay_preps)

		# For each proteome retrieved, download and validate the data files.
		for record in record_proteomes:
			for prepprot in record:
				self.metadata_from_prep(prepprot)

				yield workflows.collect(session,prepprot,result_dir,**self.options['collect'])

		# After all the proteome data included in this study is retrieved and validated,
		# create a submission summary file and submit the data to the PRIDE repository.
		yield workflows.submit(result_dir,self.project_metadata,**self.options['submit'])