#!/usr/bin/env python2
import sys
import logging
from logging import FileHandler,StreamHandler
import os
import ftplib
import sqlite3
import string
from contextlib import closing
import subprocess
import argparse
import gzip
import re
import collections
import copy
import traceback  as trace
import pdb
import server
from xml.sax.saxutils import quoteattr as xml_quoteattr

try:
	import xml.etree.cElementTree as ET
except ImportError:
	import xml.etree.ElementTree as ET
# connection information for the ucsc ftp server
ftp_server = 'hgdownload.cse.ucsc.edu'
directory = '/goldenPath/{}/database'
username = 'anonymous'
password = ''

logger = logging.getLogger('genomerunner.dbcreator')
hdlr = logging.FileHandler('genomerunner_dbcreator.log')
hdlr_std = StreamHandler()
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.addHandler(hdlr_std)
logger.setLevel(logging.INFO)

ftp = ""
illegal_chars = ['=',':']

			
# downloads the specified file from ucsc.  Saves it with a .temp extension untill the download is complete.
def download_ucsc_file(organism,filename,downloaddir):
	''' Downloads the filename from the UCSC ftp server and saves it
	in a folder with the same name as the organism.
	'''
	outputpath = ''
	if downloaddir != None and downloaddir != '':
		outputdir = os.path.join(downloaddir,organism)
	else:
		outputdir = organism
	try:
		if os.path.exists(outputdir) == False and outputdir != '':
			logger.info( "creating directory {}".format(outputdir))
			os.makedirs(outputdir)
	except Exception, e:
		logger.warning( e)
		logger.warning("Could not create folder at {} for {}".format(outputdir,filename))
		return '' 
	
	try:
		outputpath = os.path.join(outputdir,filename)
		if not os.path.exists(outputpath):
			with open(outputpath + ".temp",'wb') as fhandle:  
				global ftp
				logger.info( 'Downloading {} from UCSC'.format(filename))				
				ftp.cwd(directory.format(organism))
				ftp.retrbinary('RETR ' + "{}".format(filename),fhandle.write)
				os.rename(outputpath+".temp",outputpath)
				logger.info( 'Finished downloading {} from UCSC'.format(filename))
		else:
			logger.info( '{} already exists, skipping download'.format(outputpath))
	except Exception, e:
		logger.warning( e)
		logger.warning("Could not download the {} sql file. Names ARE case sensitive.".format(filename))
		return '' 

	return outputpath 


def download_trackdb(organism,outputdir):
	''' Downloads the trackdb.sql and trackDb.txt.gz from the UCSC ftp server and saves it in a folder with the same name as the organism.
		Returns the path of the downloaded .sql file
	'''
	sqloutputpath = download_ucsc_file(organism,"trackDb.sql",outputdir)
	dataoutpath = download_ucsc_file(organism,"trackDb.txt.gz",outputdir)
	' replace all of the \\\n characters in the html column with <br />'
	text = gzip.open(dataoutpath).read()
	with gzip.open(dataoutpath,'wb') as sw:
		sw.write(text.replace('\\\n','<br />').replace('\\\t','     '))
	return sqloutputpath


	

def _check_cols(colnames,colstoextract):
	'''checks if all the columns to extract
	actually exist in the ucsc table
	'''
	for c in colstoextract:
		if not c in colnames:
			return False
	return True


def extract_bed6(outputpath,datapath,colnames):
	colstoextract = ['chrom','chromStart','chromEnd','name','score','strand']
	# Checks if all of the columns exist in the table.  If not extract_bed5 is tried instead
	if _check_cols(colnames,colstoextract):
		logger.info( "Outpath is: {}".format(outputpath))
		with gzip.open(datapath) as dr:
			with open(outputpath,"wb") as bed:
				while True:
						line = dr.readline().strip('\r').rstrip('\n')
						if line == "":
							break
						r  = dict(zip(colnames,line.split('\t')))
						row = []
						row = [r["chrom"],r["chromStart"],r["chromEnd"],''.join(e for e in r["name"] if e.isalnum()),r["score"] if r["score"] != "." else "0",r["strand"] if r["strand"] in ["+","-"] else ""]# Can't use strand as "."
						bed.write("\t".join(map(str,row))+"\n")
	else:
		logger.warning("Nonstandard bed6, attempting extraction as bed5")
		extract_bed5(outputpath,datapath,colnames)

def extract_bed5(outputpath,datapath,colnames):
	colstoextract = ['chrom','chromStart','chromEnd','name','score']
	if _check_cols(colnames,colstoextract):
		with open(outputpath,"wb") as bed:
			with gzip.open(datapath) as dr:
				while True:
					line = dr.readline().rstrip('\r').rstrip('\n')
					if line == "":
						break
					r  = dict(zip(colnames,line.split('\t')))
					row = [r["chrom"],r["chromStart"],r["chromEnd"],''.join(e for e in r["name"] if e.isalnum()),r["score"] if r["score"] != "." else "0"] # Can't use strand as "."
					bed.write("\t".join(map(str,row))+"\n")
	else:
		logger.warning("Nonstandard bed5, attempting extraction as bed4")
		extract_bed4(outputpath,datapath,colnames)
	
def extract_bed4(outputpath,datapath,colnames):
	colstoextract = ['chrom','chromStart','chromEnd','name']
	if _check_cols(colnames,colstoextract):
		with open(outputpath,"wb") as bed:
			with gzip.open(datapath) as dr:
				while True:
					line = dr.readline().rstrip('\r').rstrip('\n')
					if line == "":
						break
					r  = dict(zip(colnames,line.split('\t')))
					row = [r["chrom"],r["chromStart"],r["chromEnd"],''.join(e for e in r["name"] if e.isalnum()).replace(": ",""),"0"] # Can't use strand as ".". Replace ": " is needed for cpgIslandExt
					bed.write("\t".join(map(str,row))+"\n")
	else:
		logger.warning("Nonstandard bed4, attempting extraction as bed3")
		extract_bed3(outputpath,datapath,colnames)

def extract_bed3(outputpath,datapath,colnames):
	colstoextract = ['chrom','chromStart','chromEnd']
	with open(outputpath,"wb") as bed:
		with gzip.open(datapath) as dr:
			while True:
				line = dr.readline().strip('\r').rstrip('\n')
				if line == "":
					break
				r  = dict(zip(colnames,line.split('\t')))
				row = [r["chrom"],r["chromStart"],r["chromEnd"],"","0"] # Can't use strand as "."
				bed.write("\t".join(map(str,row))+"\n")

def extract_psl(outputpath,datapath,colnames):
	colstoextract = ['tName','tStart','tEnd','qName','qSize','strand']
	# Checks if all of the columns exist in the table.  If not
	if _check_cols(colnames,colstoextract):
		logger.info( "Outpath is: {}".format(outputpath))
		with gzip.open(datapath) as dr:
			with open(outputpath,"wb") as bed:
				while True:
						line = dr.readline().strip('\r').rstrip('\n')
						if line == "":
							break
						r  = dict(zip(colnames,line.split('\t')))
						row = []
						row = [r["tName"],r["tStart"],r["tEnd"],''.join(e for e in r["qName"] if e.isalnum()),r["qSize"] if r["qSize"] != "." else "0",r["strand"] if r["strand"] in ["+","-"] else ""]# Can't use strand as "."
						bed.write("\t".join(map(str,row))+"\n")
	else:
		logger.warning("Nonstandard PSL format")
		
def extract_genepred(outputpath,datapath,colnames):
	colstoextract = ['chrom','txStart','txEnd','name','strand']
	exonpath = outputpath.split(".")[0]+"_exon"
	# removes the .temp file of the exon, to prevent duplicate data from being written
	if os.path.exists(exonpath+".temp"): 
		os.remove(exonpath+".temp")
	with gzip.open(datapath) as dr:
		with open(outputpath,"wb") as bed:
			with open(exonpath+".temp","wb") as exonbed:				
				while True:
					line = dr.readline().rstrip('\r').rstrip('\n')
					if line == "":
						break
					r = dict(zip(colnames,line.split('\t')))
					# extract the gene data inserts a blank for score
					row = [r['chrom'],r['txStart'],r['txEnd'],''.join(e for e in r['name'] if e.isalnum()),'0',r['strand']]
					bed.write("\t".join(map(str,row))+"\n")
					
					# extract the exon data
					for (s,e) in zip(r["exonStarts"].split(","),r["exonEnds"].split(",")):
						if s != '':
							rowexon = [r['chrom'],s,e,''.join(e for e in r['name'] if e.isalnum()),'0',r['strand']]
							exonbed.write("\t".join(map(str,rowexon))+"\n")
	# sort the file and convert to bgzip format
	sort_convert_to_bgzip(exonpath+".temp",exonpath + ".bed.gz")

def sort_convert_to_bgzip(path,outpath):
	logger.info("Converting {} to bgzip format.".format(path))
	script = "sort -k1,1 -k2,2n -k3,3n " + path +" | bgzip -c > " + outpath + ".gz.temp"
	out = subprocess.Popen([script],shell=True,stdout=subprocess.PIPE)
	out.wait()
	os.remove(path)# remove the .temp file extension to activate the GF		
	os.rename(outpath+".gz.temp",outpath)

def extract_rmsk(outputpath,datapath,colnames):
	colstoextract = ['genoName','genoStart','genoEnd','repClass', 'strand','swScore']
	with open(outputpath,"wb") as bed:
		with open(datapath) as dr:
			while True:
				line = dr.readline().strip('\r').rstrip('\n')
				if line == "":
					break
				r = dict(zip(colnames,line.split('\t')))
				row = [r["genoName"],r["genoStart"],r["genoEnd"],''.join(e for e in r["repClass"] if e.isalnum()),r["swScore"],r["strand"]]
				bed.write("\t".join(map(str,row))+"\n")

def get_column_names(sqlfilepath):
	''' extracts the column names from the .sql file and returns them
	'''
	tdbsql = open(sqlfilepath).read()
	# creates a tuple containing the column names
	tbdcolumns = re.findall("\n\s\s`*(.+?)`*\s", tdbsql, re.DOTALL)
	tbdcolumns = [c for c in tbdcolumns if not c=="KEY"]
	return tbdcolumns	

# The different file types that can be extracted.
# To add a new type add a new entry into this dictionary along with 
# the name of the function that should be used to extract the data.
preparebed = {"bed 6" : extract_bed6,
				"broadPeak": extract_bed6,
				"bed 6 +" : extract_bed6,
				"bed 12 +": extract_bed6,
				"bed 12 .": extract_bed6,
				"bed 12": extract_bed6,
				"bed 10": extract_bed6,
				"bed 9 +": extract_bed6,
				"bed 9 .": extract_bed6,
				"bed 9": extract_bed6,
				"bed 8 +": extract_bed6,
				"bed 8 .": extract_bed6,
				"bed 6 .": extract_bed6,
				"bed 5 +": extract_bed5,
				"bed 5 .": extract_bed5,
				"bed 5": extract_bed5,
				"bed5FloatScore": extract_bed5,
				"bed 4 +": extract_bed4,
				"bed 4 .": extract_bed4,
				"bed 4": extract_bed4,
				"bed 3 +": extract_bed3,
				"bed 3 .": extract_bed3,
				"bed 3" : extract_bed3,
				"genePred xenoRefPep xenoRefMrna": extract_genepred,
				"genePred vegaPep": extract_genepred,
				"genePred sgpPep": extract_genepred,
				"genePred refPep refMrna": extract_genepred,
				"genePred nscanPep": extract_genepred,
				"genePred knownGenePep knownGeneMrna": extract_genepred,
				"genePred genscanPep": extract_genepred,
				"genePred geneidPep": extract_genepred,
				"genePred ensPep": extract_genepred,
				"genePred acemblyPep acemblyMrn": extract_genepred,
				"genePred acemblyPep acemblyMrna": extract_genepred,
				"genePred" : extract_genepred,
				"psl" : extract_psl,
				"psl ." : extract_psl,
				"psl est" : extract_psl,
				"psl protein" : extract_psl,
				"psl xeno" : extract_psl,
				"rmsk" : extract_rmsk,
				"factorSource" : extract_bed6}
				
numdownloaded = collections.defaultdict(int)

def encodePath(line): # Generating paths for the ENCODE data tables using groups, tiers, and cell types
	ENCODE = re.compile('AffyRnaChipFiltTransfrags|BroadHistone|BroadHmm|GisChiaPet|GisRnaPet|HaibMethyl450|HaibGenotype|HaibMethylRrbs|HaibTfbs|OpenChromSynth|RikenCage|SunyAlbanyGeneSt|SunyAlbanyTiling|SunyRipSeq|SunySwitchgear|UmassDekker5C|UwAffyExonArray|UwDgf|UwDnase|UwHistone|UwRepliSeq|UwTfbs|CshlLongRnaSeq|CshlShortRnaSeq|LicrHistone|LicrTfbs|PsuHistone|PsuTfbs')
	CELLS1 = re.compile('Gm12878|K562|H1hesc')
	CELLS2 = re.compile('A549|Cd20ro01778|Cd20ro01794|Cd20|H1neurons|Helas3|Hepg2|Huvec|Imr90|Lhcnm2|Mcf7|Monocd14ro1746|Sknsh')
	CELLS3 = re.compile('Ag04449|Ag04450|Ag09309|Ag09319|Ag10803|Aoaf|Aosmc|Be2c|Bj|Caco2|Cmk|Dnd41|Ecc1|Gm06990|Gm12801|Gm12864|Gm12865|Gm12872|Gm12873|Gm12875|Gm12891|Gm12892|Gm19239|H7es|Hac|Hae|Hah|Hasp|Hbmec|Hcfaa|Hcf|Hcm|Hcpe|Hct116|Hee|Hek293|Hffmyc|Hff|Hgf|Hipe|Hl60|Hmec|Hmf|Hmvecdblad|Hnpce|Hpae|Hpaf|Hpdlf|Hpf|Hrce|Hre|Hrpe|Hsmmfshd|Hsmmtubefshd|Hsmmt|Hsmm|Htr8|Hvmf|Jurkat|Lncap|M059j|Mcf10aes|Nb4|Nha|Nhbe|Nhdfad|Nhdfneo|Nhek|Nhlf|Nt2d1|Osteobl|Osteo|Ovcar3|Panc1|Panislets|Pfsk1|Prec|Progfib|Rpmi7951|Rptec|Saec|Skmc|Sknmc|Sknshra|T47d|Th1|Th2|U87|Werirb1|Wi38')
	n = ENCODE.search(line) 
	m1 = CELLS1.search(line)
	m2 = CELLS2.search(line)
	m3 = CELLS3.search(line)
	if n:
		grp = n.group()
	else:
		grp = 'Special'
	if m1:
		Tier = 'Tier1'
		Cell = m1.group()
	elif m2:
		Tier = 'Tier2'
		Cell = m2.group()
	elif m3:
		Tier = 'Tier3'
		Cell = m3.group()
	else:
		Tier = ''
		Cell = ''
	return os.path.join('ENCODE', grp, Tier, Cell, line.strip())		

def create_feature_set(trackdbpath,organism,max_install):
	outputdir = os.path.dirname(trackdbpath)
	trackdb = load_tabledata_dumpfiles(os.path.splitext(trackdbpath)[0])
	prog, num = 0,len(trackdb)
	added_features = [] 
	notsuptypes, outpath = set([]),""
	for row in trackdb:
		logger.info( 'Processing files {} of {}'.format(prog,num))
		if row['type'] in preparebed:
			# this line limits the number of GRF to download
			if numdownloaded[row["type"]] <= max_install or max_install == None:
				sqlpath = download_ucsc_file(organism,row["tableName"] + ".sql","downloads")
				download_ucsc_file(organism,row["tableName"] + ".txt.gz","downloads")
				if sqlpath != '':
					logger.info( "converting"+row['tableName']+ " into proper bed format")
					try:
						if row["tableName"].startswith("wgEncode"):
							outpath = os.path.join(outputdir, encodePath(row["tableName"]))
						else:
							outpath = os.path.join(outputdir,row["grp"],row["tableName"]) # ,'Tier' + row["visibility"]
						if not os.path.exists(os.path.dirname(outpath)):
							os.makedirs(os.path.dirname(outpath))
						if os.path.exists(outpath + ".bed.gz") == False:
							# removes the .temp file, to prevent duplicate data from being written
							if os.path.exists(outpath+".temp"):
								os.remove(outpath+".temp")
							# converts the ucsc data into propery bed format
							logger.info( "Converting into proper bed format. {}".format(os.path.splitext(sqlpath)[0]))
							preparebed[row["type"]](outpath+".temp",os.path.splitext(sqlpath)[0]+".txt.gz",get_column_names(os.path.splitext(sqlpath)[0]+".sql"))

							# sort the file and convert to bgzip format
							o_dir = os.path.dirname(outpath)
							new_path = os.path.join(o_dir,''.join(e for e in os.path.basename(outpath) if e.isalnum() or e=='.' or e=='_')) + ".bed.gz"
							sort_convert_to_bgzip(outpath+".temp",new_path)
							added_features.append(outpath)
						else:
							logger.info( "{} already exists as or .gz, skipping extraction".format(outpath.replace(".gz","")))							
						numdownloaded[row["type"]] += 1
					except Exception, e:
						exc = trace.format_exc()
						logger.warning( "Unable to convert {} into bed".format(row["tableName"]))
						logger.warning(exc)
						continue
		else:
			if 'big' not in row['type']:
				notsuptypes.add(row['type'])

		prog += 1
		# cleanup the temporary files
		if os.path.exists(outpath + ".temp"): os.remove(outpath+".temp")

	logger.info( "The following types are not supported (includes all 'big' file types):\n " + str(notsuptypes))
	logger.info("The following features were added to the database: \n{}".format(added_features))
	logger.info("A count of features added by type: ")
	for k,d in numdownloaded.iteritems():
		logger.info( k + ":" + str(d))
	return "created database"
	
def create_single_feature(trackdbpath,organism,feature):
	''' Downloads a single feature and adds it to the genomerunner flat file database'''

	outputdir = os.path.dirname(trackdbpath)
	trackdb = load_tabledata_dumpfiles(os.path.splitext(trackdbpath)[0])
	f_type = _gettype(feature,trackdb)
	f_info = _get_info(feature,trackdb)
	# is the feature in trackDb
	if f_info != False:
		# is the feature type supported by the dbcreator
		if  f_type in preparebed:
			sqlpath = download_ucsc_file(organism,f_info["tableName"] + ".sql","downloads")
			download_ucsc_file(organism,f_info["tableName"] + ".txt.gz","downloads")
			if sqlpath != '':
				logger.info( "converting"+f_info['tableName']+ " into proper bed format")
				try:
					if f_info['tableName'].startswith("wgEncode"):
						outpath = os.path.join(outputdir, encodePath(f_info["tableName"]))
					else:
						outpath = os.path.join(outputdir,f_info["grp"],f_info["tableName"]) #'Tier' + f_info["visibility"],
					if not os.path.exists(os.path.dirname(outpath)):
						os.makedirs(os.path.dirname(outpath))
					# if the feature is not in the database, add it
					if os.path.exists(outpath + ".bed.gz") == False:
						# removes the .temp file, to prevent duplicate data from being written
						if os.path.exists(outpath+".temp"):
							os.remove(outpath+".temp")
						# converts the ucsc data into proper bed format
						logger.info( "Converting {} into proper bed format.".format(os.path.splitext(sqlpath)[0]))
						preparebed[f_info["type"]](outpath+".temp",os.path.splitext(sqlpath)[0]+".txt.gz",get_column_names(os.path.splitext(sqlpath)[0]+".sql"))

						# sort the file and convert to bgzip format
						o_dir = os.path.dirname(outpath)
						new_path = os.path.join(o_dir,''.join(e for e in os.path.basename(outpath) if e.isalnum() or e=='.' or e=='_')) + ".bed.gz"
						sort_convert_to_bgzip(outpath+".temp",new_path)
					else:
						logger.info( "{} already exists, skipping extraction".format(outpath))
					numdownloaded[f_info["type"]] += 1
				except Exception, e:
					exc = trace.format_exc()
					logger.warning( "Unable to convert {} into bed".format(f_info["tableName"]))
					logger.warning(exc)
		else:
			logger.warning("{} is a type {}, which is not supported".format(feature,f_type))
	else:
		logger.warning( "Could not find {} in trackDb".format(feature))

def _gettype(feature,trackdb):
	'''Returns the type of feature from the trackdb'''
	for x in trackdb:
		if x['tableName'] == feature:
			return x['type']

def _get_info(feature,trackdb):
	''' Returns the row in trackdb that contains the feature information'''
	for t in trackdb:
		if feature == t['tableName']:
			return t
	return False

def load_tabledata_dumpfiles(datapath):
	''' Loads the table data into memory from the sql file and the .txt.gz file
	data path should be WITHOUT extension (example. home/trackDb
	'''
	colnames = get_column_names(datapath+".sql")
	data = list()	
	with gzip.open(datapath+'.txt.gz') as fhandle:
		while True:
			line = fhandle.readline()
			if line == "":
				break
			row  = dict(zip(colnames,line.split('\t')))
			data.append(row)
	return data


def create_galaxy_xml_files(db_dir,outputdir):
	if not os.path.exists(db_dir):
		logger.error("Database does not exist at {}".format(db_dir))
		return
	orgs = os.walk(db_dir).next()[1] # get organism names
	xml_path = os.path.join(outputdir, "grsnp_gfs.xml")
	with open(xml_path,"wb") as writer:
		for o in orgs:
			blacklist = []
			# read in names of tracks to ignore
			blacklist_path = os.path.join(db_dir,o,"blacklist.txt")
			if os.path.exists(blacklist_path):
				with open(blacklist_path) as f:
					blacklist = [line.strip() for i,line in enumerate(f)]

			# generate the xml file for galaxy's checkbox tree
			writer.write("""<filter type="data_meta" data_ref="input_gfs" meta_key="dbkey" value="{}">\n\t<options>\n""".format(o))
			tmp = dir_as_xml(os.path.join(db_dir,o),blacklist).split("\n")
			tmp = "\n".join(tmp[1:-2]) # remove the first 'option' entry as this is the organism directory
			writer.write(tmp + "</options>\n</filter>") 
	logger.info("Created galaxy xml file {}".format(xml_path))		

def base_name(k):
    return os.path.basename(k).split(".")[0]		


def dir_as_xml(path, blacklist):
	''' Code adapted from
	 from: http://stackoverflow.com/questions/2104997/os-walk-python-xml-representation-of-a-directory-structure-recursion
	'''
	result = '<option name={} value={}>\n'.format(xml_quoteattr(os.path.basename(path))
													,xml_quoteattr(path))
	for item in os.listdir(path):
		itempath = os.path.join(path, item)
		if os.path.isdir(itempath):
			result += '\n'.join('  ' + line for line in 
			dir_as_xml(os.path.join(path, item),blacklist).split('\n'))
		elif os.path.isfile(itempath) and itempath.endswith(".bed.gz") and base_name not in blacklist:
			result += '  <option name={} value={}/>\n'.format(xml_quoteattr(base_name(item)), xml_quoteattr(os.path.join(path,item)))
	result += '</option>\n'
	return result



if __name__ == "__main__":
	parser = argparse.ArgumentParser(prog="python -m grsnp.dbcreator", description='Creates the GenomeRunner SNP Database. Example: python -m grsnp.dbcreator -d /home/username/grs_db/ -g mm9', epilog='IMPORTANT: Execute DBCreator from the database folder, e.g., /home/username/grs_db/. Downloaded files from UCSC are placed in ./downloads database created in ./grsnp_db.')
	parser.add_argument("--data_dir" , "-d", nargs="?", help="Set the directory where the database to be created. Use absolute path. Example: /home/username/grs_db/. Required", required=True)
	parser.add_argument('--organism','-g', nargs="?", help="The UCSC code of the organism to use for the database creation. Default: hg19 (human). Required", default="hg19")
	parser.add_argument('--featurename','-f', nargs="?", help='The name of the specific genomic feature track to create (Example: knownGene)')
	parser.add_argument('--max','-m', nargs="?", help="Limit the number of features to be created within each group.",type=int)
	parser.add_argument('--galaxy', help="Create the xml files needed for Galaxy. Outputted to the current working directory.", action="store_true")

	args = vars(parser.parse_args())

	if not args["data_dir"]:
		print "ERROR: --data_dir is required"
		sys.exit()


	global ftp, max_install_num
	ftp = ftplib.FTP(ftp_server)
	ftp.login(username,password)
	outputdir=os.path.join(args["data_dir"],'grsnp_db')

	if args['galaxy']:
		usrdir = raw_input("Enter directory of Galaxy. If left blank, grsnp_gfs.xml file will be outputted in the cwd: \n")
		if usrdir == '': usrdir = os.getcwd()
		create_galaxy_xml_files(outputdir,usrdir)		
		sys.exit()
	if args['organism'] is not None and args['featurename'] is None: # Only organism is specified. Download all organism-specific features
		trackdbpath = download_trackdb(args['organism'],outputdir)
		create_feature_set(trackdbpath,args['organism'],args["max"])
	elif args['organism'] is not None and args['featurename'] is not None: # Both organism and feature name are specified. Download this feature for a given organism
		trackdbpath = download_trackdb(args['organism'],outputdir)
		create_single_feature(trackdbpath,args['organism'],args['featurename'])
	elif args['organism'] is None and args['featurename'] is not None: # Warning in case of only feature name is supplied
		print "To add a specific feature to the local database, please supply an organism assembly name"
	else:
		print "ERROR: Requires UCSC organism code.  Use --help for more information"
		sys.exit()
	



	root_dir = os.path.dirname(os.path.realpath(__file__))
	readme = open(os.path.join(root_dir,"grsnp_db_readme.txt")).read()
	with open("grsnp_db_readme.txt","wb") as writer:
		writer.write(readme)
	print "FINISHED: Downloaded files from UCSC are placed in {}.  Database created in {}".format(os.path.join(args["data_dir"],"downloads"),os.path.join(args["data_dir"],"grsnp_db`"))