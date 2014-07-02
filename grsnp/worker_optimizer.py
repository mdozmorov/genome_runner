from celery import Celery
from celery import signals
import grsnp.hypergeom4 as hpgm
from celery.bin import Option
from celery.exceptions import Reject
import os


# celery
app = Celery('grsnp')
app.config_from_object('grsnp.celeryconfiguration_optimizer')
app.user_options['preload'].add(
    Option('-d', '--data_dir', default='',
           help='Set the directory containing the database. Required. Use absolute path. Example: /home/username/db_#.##_#.##.####/.'),
)

sett = {}

# acks_late allows us to remove jobs for which we do not have the corresponding data
@app.task(acks_late=True,ignore_result = False)
def calculate_bkg_gf_overlap(gf_path=None,list_bkg_paths=None):
	"""Calculates the overlaps stats between the genomic feature and the backgrounds provided.

	gf_path: The relative path to the genomic feature bed file. EX: 'grsnp_db_75_plus/hg19/genes/evofold.bed.gz'
	list_bkg_paths: A list containing relative paths to the backgrounds. EX: ['custom_data/backgrounds/hg19/bkg1.gz','custom_data/backgrounds/hg19/bkg2.gz']
	"""
	global sett
	data_dir = sett["data_dir"]
	full_gf_path = os.path.join(data_dir,gf_path)
	full_bkg_paths = [os.path.join(data_dir,x) for x in list_bkg_paths]
	try:
		missing_files = get_missing_files([full_gf_path] + list_bkg_paths)
		if not missing_files:
			gf_bgs_stats = hpgm.get_overlap_statistics(full_gf_path,list_bkg_paths)
			return {full_gf_path: gf_bgs_stats}		
		else:
			raise Exception("gf/background data files not found: " + str(missing_files))
	except Exception as exc:
		raise Reject(ex)

# process command line arguments if they exist
@signals.user_preload_options.connect
def cmd_options(options,**kwargs):
	global sett
	sett["data_dir"] = options['data_dir']



def get_missing_files(paths):
	'''Returns a list of any files that are missing. Returns false if all files are there.
	'''
	missing_files = False
	for f in paths:
		if not os.path.exists(f):
			missing_files.append(f)
	if missing_files:
		return missing_files
	else:
		return False

