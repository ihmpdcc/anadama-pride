import os
import sys
import inspect
import subprocess
import re
from collections import OrderedDict
from urlparse import urlparse

import cutlass.aspera as asp

file_mapping=OrderedDict([
	("file_id", list()),
	("file_type", list()),
	("file_path", list()),
	("file_mapping", list()),
])

sample_metadata=OrderedDict([
	("file_id", list()),
	("species", list()),            # Field 'species' from
									# corresponding assey_prep
	("tissue", list()),             # Field 'tissue' from
									# corresponding assey_prep
	("instrument", list()),         # Field 'instrument_name' from
									# proteome OSDF entry
	("experimental_factor", list()) # Field 'exp_description' from
									# proteome OSDF entry
])

# Called for each assay_prep present in the study to download and validate files
# from each proteome instance included in the assay_prep.
def collect(session, prepprot, result_dir, dcc_user, dcc_pw, study_id):

	# Utility function to update the File Mapping section of submission.px file
	def update_file_mapping(file_type, file_name, result_id=0):
		id = len(file_mapping["file_id"]) + 1
		file_mapping["file_id"].append(id)
		file_mapping["file_type"].append(file_type)
		file_mapping["file_path"].append(result_dir+'/'+file_name)

		if(file_type=="raw"):
			mapping=str(result_id)+':'+str(id)
			file_mapping["file_mapping"].append(mapping)

	# Utility function to update the Sample Metadata section of submission.px file
	def update_sample_metadata(result_id,proteome):
		sample_metadata["file_id"].append(result_id)
		sample_metadata["species"].append(prepprot.prep._species)
		sample_metadata["tissue"].append(prepprot.prep._tissue)
		sample_metadata["instrument"].append(proteome._instrument_name)
		#sample_metadata["modification"].append('MOD,MOD:00394,acetylated residue,')
		sample_metadata["experimental_factor"].append(proteome._exp_description)

	# Utility function to download files from the url present in the proteome instances in OSDF
	def download_file(file_url):
		url = urlparse(file_url)
		file_path = url.path.split('/')
		if not os.path.exists(result_dir+'/'+file_path[len(file_path)-1]):
			print 'Downloading file '+file_path[len(file_path)-1]+' to '+result_dir
			if asp.download_file(url.netloc, dcc_user, dcc_pw, url.path, result_dir):
				print 'Download Complete'
				return file_path[len(file_path)-1]
			else:
				print 'Unable to download file ' + file_path[len(file_path)-1]
				sys.exit(1)

	# Utility function to download files from a single proteome instance and update the meatadata
	# fields to be included in the submission.px file.
	# Note: Assuming that only one result set (i.e. one mzid result file and its corresponding
	# single peak and raw files) is present per proteome instance in OSDF
	def download_files():
		result_id = 0
		file_name=None
		result_file=None
		peak_file=None
		for url in proteome._result_url:
			result_file = download_file(url)
			if not result_file is None:
				result_id = len(file_mapping["file_id"]) + 1
				update_file_mapping('result', result_file)
				update_sample_metadata(result_id, proteome)
				break

		for url in proteome._peak_url:
			peak_file = download_file(url)
			if not peak_file is None:
				# Validating that the peak file format is '.mgf'
				if not peak_file.lower().endswith('.mgf'):
					print 'Peak File is required to be in .mgf format'
					sys.exit(1)
				update_file_mapping('peak', peak_file)
				break

		for url in proteome._raw_url:
			file_name = download_file(url)
			if not file_name is None:
				update_file_mapping('raw', file_name, result_id)

		if not len(proteome._other_url) == 0:
			for url in proteome._other_url:
				file_name = download_file(url)
				if not file_name is None:
					update_file_mapping('raw', url, result_id)

		return result_file,peak_file

	def validate_files(result_file, peak_file,proteome):
		print 'Validating Proteome '+proteome._id
		code_dir=os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))+'/pg-converter-1.2/pg-converter.jar'
		return_code=subprocess.check_output(['java','-jar',code_dir,'-v','-mzid',result_dir+'/'+result_file,'-peak',result_dir+'/'+peak_file,
		                                     '-skipserialization','-reportfile',result_dir+'/'+'validation_result_'+proteome._id+'.txt'])
		tag_check_list = ['Total proteins','Total peptides','Total spectra']
		with open(result_dir+'/'+'validation_result_'+proteome._id+'.txt') as _file:
			for line in _file.readlines():
				tags=line.strip('\n').split(':')
				if tags[0] in tag_check_list and int(tags[1].strip(' '))<1:
					print tags[0], ' cannot be found for proteome ', proteome._id
					print 'Chceck submission folder for related validation test result file.'
					# sys.exit(1)
				if tags[0]=='Status' and tags[1].strip(' ') != 'OK':
					print 'Result file could not be validated for proteome ', proteome._id
					print 'Chceck submission folder for related validation test result file.'
					sys.exit(1)
		_file.close()
		try:
			os.remove(result_dir+'/'+'validation_result_'+proteome._id+'.txt')
		except OSError, e:
			print ("Error removing validation result file: %s - %s." % (e.filename, e.strerror))
		print 'Validated. Ok!'

	for proteome in prepprot.proteome:
		result_file, peak_file = download_files()
		validate_files(result_file,peak_file,proteome)

# Function that creeates the submission.px file and then submits data to the PRIDE repository
def submit(result_dir,project_metadata,pride_user,pride_pw,pride_server,pride_directory):
	os.chdir(result_dir)

	def fill_list_type_metadata(submission_file,data):
		data_string='['
		for item in data:
			data_string += str(item)
		data_string += ']'
		submission_file.write(data_string)

	# Utility function to create and populate the submission.px file
	def _create_submission_file():
		submission_file_name = 'submission.px'
		try:
			os.remove(submission_file_name)
			print 'Removing old submission file'
		except OSError:
			pass

		submission_file = open(submission_file_name, "a+")
		# Adding Project Metadata to the summary file.
		for entry in project_metadata:
			data = project_metadata[entry]
			if (type(data) is str):
				submission_file.write('MTD\t' + entry + '\t' + project_metadata[entry] + '\n')
			else:
				data_string = 'MTD\t' + entry + '\t['
				for item in data:
					data_string += str(item)
				data_string += ']\n'
				submission_file.write(data_string)

		# Adding File Mapping data to the summary file.
		submission_file.write('\nFMH\t')

		for entry in file_mapping:
			submission_file.write(entry+'\t')
		submission_file.write('\n')

		for id in file_mapping["file_id"]:
			submission_file.write('FME\t'+str(id)+'\t'+file_mapping["file_type"][id-1]+'\t'+file_mapping["file_path"][id-1]+'\t')
			if(file_mapping["file_type"][id-1]=="result"):
				for mapping in file_mapping["file_mapping"]:
					splits=mapping.split(':')
					if splits[0]==str(id):
						submission_file.write(splits[1]+',')
			submission_file.write('\n')

		# Adding Sample Metadata to the result file.
		submission_file.write('\nSMH\t')

		for entry in sample_metadata:
			submission_file.write(entry + '\t')
		submission_file.write('\n')

		for id in range(len(sample_metadata["file_id"])):
			submission_file.write('SME\t')
			submission_file.write(str(sample_metadata["file_id"][id])+'\t')
			fill_list_type_metadata(submission_file,sample_metadata["species"][id])
			submission_file.write('\t')
			fill_list_type_metadata(submission_file, sample_metadata["tissue"][id])
			submission_file.write('\t')
			fill_list_type_metadata(submission_file, sample_metadata["instrument"][id])
			submission_file.write('\t')

			submission_file.write(sample_metadata["experimental_factor"][id])
			submission_file.write('\n')

		submission_file.close()

	# Utility function to submit all the data and submission summary file to PRIDE cia ASPERA
	def _submit_data():
		environ=os.environ.copy()
		# Set the environment password for ASPERA transfers as the one provided by the user.
		environ['ASPERA_SCP_PASS'] = pride_pw
		# The command used to submit data to PRIDE.
		# print "ascp", "-QT", "-l500M", "--file-manifest=text", "-k", "2", "-o", "Overwrite=diff", result_dir, pride_user + '@' + pride_server + ':/' + pride_directory
		try:
			ascp_cmd=["ascp","-QT", "-l500M", "--file-manifest=text", "-k", "2", "-o", "Overwrite=diff", result_dir, pride_user+'@'+pride_server+':/'+pride_directory]
			process = subprocess.Popen(ascp_cmd, stdout=subprocess.PIPE,
			                           stdin=subprocess.PIPE,
			                           stderr=subprocess.PIPE,
			                           universal_newlines=True,
			                           env=environ)

			(s_out, s_err) = process.communicate()
			rc = process.returncode

			if rc == 0:
				print("Aspera ascp utility returned successful exit value.")
			else:
				if re.match(r"^.*failed to authenticate", s_err):
					print("Aspera authentication failure.")
				else:
					if s_err != None:
						print("Unexpected STDERR from ascp: %s" % s_err)
					if s_out != None:
						print("Unexpected STDOUT from ascp: %s" % s_out)

		except subprocess.CalledProcessError as cpe:
			print("Encountered an error when running ascp: ", cpe)


	_create_submission_file()
	_submit_data()