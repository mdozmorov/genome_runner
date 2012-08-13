#!/usr/bin/env python
import sys, operator, os, numpy
from numpy import random as rand
from pybedtools import BedTool
from pybedtools.featurefuncs import midpoint as pb_midpoint
import pybedtools
from collections import namedtuple
import cPickle
import logging
from logging import FileHandler,StreamHandler
from path import basename
import json
import copy
import traceback  as trace

logger = logging.getLogger('genomerunner.query')
hdlr = logging.FileHandler('genomerunner_server.log')
hdlr_std = StreamHandler()
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
# This line outputs logging info to the console
#logger.addHandler(hdlr_std)
logger.setLevel(logging.INFO)



# This class represents an Enrichment analysis result
# Lists of Enrichment objects are serialized to a Python Pickle
# file when an analysis is complete	
_Enrichment = namedtuple("Enrichment",
		["A","B","nA","nB","observed","expected","p_value","obsprox","expprox","pybed_p_value","pybed_expected","jaccard_observed","jaccard_p_value","jaccard_expected","proximity_p_value"])
class Enrichment(_Enrichment):
	def category(self):
		if self.expected == 0 or self.p_value > 0.05:
			return "nonsig"
		elif self.observed < self.expected:
			return "under"
		else:
			return "over"

def make_filter(name, score, strand):
	def filter(interval):
		if name and name != interval.name:
			return False
		if score and score > int(interval.score):
			return False
		if strand and strand != interval.strand:
			return False
		return True
	return filter

# TODO implement remove_invalid and report results to user.  
def enrichment(id,a, b,background, organism,name=None, score=None, strand=None, n=10):
	"""Perform enrichment analysis between two BED files.

	a - path to Feature of Interest BED file
	b - path to Genomic Feature BED file
	n - number of Monte-Carlo iterations
	"""

	A = BedTool(str(a))
	B = BedTool(str(b))
	genome = pybedtools.get_chromsizes_from_ucsc(organism)
	genome_fn = pybedtools.chromsizes_to_file(genome)


	organism = str(organism)
	flt = make_filter(name,score,strand)
	B.filter(flt).saveas()
	nA = len(A)
	nB = len(B)
	if not nA or not nB:
		return Enrichment(a,basename(b),nA,nB,0,0,1,0,0,1,0,0,1,0)

	A.set_chromsizes(genome)
	B.set_chromsizes(genome)
	obs = len(A.intersect(B, u=True))
	# This is the Monte-Carlo step.  If custom background present, it is used
	logger.info("RUNNING MONTE CARLO ({}): (id={})".format(b,id))
	write_progress(id, "Running Monte Carlo {}".format(b))
	dist = [len(shuffle(a,background,organism).intersect(B, u=True)) for i in range(n)]
	exp = numpy.mean(dist)
	# gave p_value a value here so that it doesn't go out of scope, is this needed?
	p_value = 'NA'
	if exp == obs or (exp == 0 and obs == 0):
		p_value =1
	else:
		p_value = len([x for x in dist if x > obs]) / float(len(dist))
		p_value = min(p_value, 1 - p_value)
	
	# expected caluclated using pybed method CANNOT use custom background
	logger.info("RUNNING RANDOM INTERSECTIONS ({}): (id={})".format(b,id))
	write_progress(id, "Running Random Intersections: {0}".format(b))
	pybeddist = A.randomintersection(B,iterations=n,shuffle_kwargs={'chrom': True})
	pybeddist = list(pybeddist)
	pybed_exp = numpy.mean(pybeddist)
	pybedp_value = 'NA'
	if pybed_exp == obs or (pybed_exp == 0 and obs == 0):
		pybedp_value =1
	else:
		pybedp_value = len([x for x in pybeddist if x > obs]) / float(len(pybeddist))
		pybedp_value = min(pybedp_value,1-pybedp_value)
	# epected calculated using jaccard method
	A2 = A.cut([0,1,2])
	B2 = B.cut([0,1,2])
	logger.info("Running Jaccard ({}): (id={})".format(b,id))
	write_progress(id, "Running Jaccard {}".format(b))

	resjaccard = A2.naive_jaccard(B2,genome_fn=genome_fn,iterations=n,shuffle_kwargs={'chrom':True})
	jaccard_dist = resjaccard[1]
	jaccard_obs = resjaccard[0]
	jaccard_exp = numpy.mean(resjaccard[1])
	jaccardp_value = 'NA'
	if jaccard_exp == jaccard_obs or (jaccard_exp  == 0 and jaccard_obs == 0):
		jaccardp_value =1
	else:
		jaccardp_value = len([x for x in jaccard_dist if x > jaccard_obs]) / float(len(jaccard_dist))
		jaccardp_value = min(jaccardp_value,1-jaccardp_value)

	
	# run proximity analysis
	if True:
		logger.info("Running proximity {} (id={})".format(b,id))
		#stores the means of the distances for the MC
		expall =[]
		for i in range(n):
			tmp = shuffle(a,background,organism).closest(B,d=True)
			# get the distances
			for t in tmp:
				expall.append(t[-1])
		# calculate the overal expected distance
		expall.append(numpy.mean(numpy.array(expall,float)))
		print expall
		print "There are {}:".format(len(expall))
		# calculate the expected mean for all of the runs
		expprox = numpy.mean(numpy.array(expall,float))	
		# proximety analysis for observed
		tmp = A.closest(B,d=True)
		obsall = []
		for t in tmp:
			obsall.append(t[-1])
		obsprox = numpy.mean(numpy.array(obsall,float))
		proximityp_value = len([x for x in expall if x > obsprox]) / float(len(expall))
		print "proximity pvalue" + str(proximityp_value)
		proximityp_value = min(proximityp_value,1-proximityp_value)
	else:
		print "Skipping Proximity"
		obsprox = -1
		expprox = -1

	return Enrichment(a, basename(b), nA, nB, obs, exp, p_value,obsprox,expprox,pybedp_value,pybed_exp,jaccard_obs,jaccardp_value,jaccard_exp,proximityp_value)

def shuffle(bed_file, background_bed,organism):
	""" Accepts a file path to a bed file and a background file
	Random intervals are generate from the intervals in the background
	file.  An attempt is made to make the new random intervals the same size
	as the original intervals. One new interval is generated per interval in the
	bed file.

	If no background is provided, The pybedtool internal shuffle function is called
	and the entire genome is used as background
	"""
	A =  BedTool(bed_file)
	if background_bed != "":
		B = BedTool(background_bed)
		rand_a = ""
		for a in A:
			a_len = a.length
			r = rand.random_integers(0,len(B)-1)
			# if cur A length is greater than random background inteval
			# the new randA is set to be same size as background inteval
			if  a_len > B[r].length:
				rand_a += "\t".join(B[r][:4]) +"\t" + "\t".join(a[4:])+"\n"
			else:
				randstart = rand.random_integers(B[r].start,B[r].end - a_len)
				rand_a += "\t".join([B[r].chrom,str(randstart),str(randstart+a_len),
					B[r].name,
					"\t".join(a[4:])]) + "\n"	
		rand_A = BedTool(rand_a,from_string=True)
		return rand_A
	else:
		return A.shuffle(genome=organism,chrom=True)

def genome_tri_corr(A_bedtool, B_bedtool,genome):
	''' Based on Genometric Correlation algorithm at http://genometricorr.sourceforge.net/
		Genome file is a dictionary of chroms and chrom lengths.  Can be retrieved from ucsc
		by calling pybedtool.get_chromsizes_from_ucsc('hg19'). Where hg19 is the 
		assembly name
	'''
	# generate the midpoint intervals
	midpoint_A = A_bedtool.each(_midpoint)
	stitched_B = stitch_midpoints(B_bedtool,genome)
	d_i_all = []
	for a in midpoint_A:
		# get the B intervals that overlap a.
		inter_b = stitched_B(a)
		shortest_b = 'a'
		# gets the shortest returned interval
		for x in inter_b:
			if len(x) < shortest_b:
				shortest_b = x
		print "Shortest overlap interval: " 
		print shortest_b
		# calculates the numorator of the d_i equation
		d_i = min(a-shortest_b.start,b-shortest_b.end - a)
		print "d_i numerator: "
		print d_i
		# calculates d_i
		d_i = d_i/len(shortest_b)
		print "d_i"
		print d_i
		d_i_all.append(d_i)




def stitch_midpoints(B_bedtool,genome):
	''' Gets the midpoints of the intervals and creates a new set of connected intervals from the midpoints.
	One set of intervals is created per strand
	'''
	strands = ["+","-",["","."," "]]
	midpoints = [] 
	B_bedtool = B_bedtool.sort()
	# cycles through each strand for each chrom
	B_bedtool = B_bedtool.each(pb_midpoint)
	for chrom in genome.keys():
		chrom_B = B_bedtool.filter(lambda x: x.chrom =="chr1").saveas()
		chrom_B.saveas()
		print chrom_B
		if len(chrom_B) == 0:
			continue
		for s in strands:
			strand_chrom_B = chrom_B.filter(lambda x: x.strand in "+").saveas()
			strand_chrom_B.saveas()
			# set the endpoint equal to the start of upstream interval start
			if len(strand_chrom_B) == 0:
				continue
			for i in range(1,len(strand_chrom_B)-1):
				print "BEFORE{}".format(strand_chrom_B[i].end)
				strand_chrom_B[i].end = strand_chrom_B[i+1].start	
				print "AFTER{}".format(strand_chrom_B[i].end)
			#print strand_chrom_B
			#extends the first interval to the start of chromosome
			# extends the last interval to the end of the chromosome
			#strand_chrom_B[len(strand_chrom_b)-1].end = genome[chrom][1]
			print "ADDING!"
			print strand_chrom_B
			midpoints.append(strand_chrom_B)
	
	#concat all the interval sets from different chroms together
		#TODO can a bed tool be declared ahead of time? Then the 0 index doesn't have to be accessed before 
	midpoints_B = midpoints[0]
	for i in range(1,len(midpoints)-1):
		midpoints_B.cat(midpoints[i],post_merge=False)

	return midpoints_B


def _midpoint(interval):
	''' Uses pybedtools midpoint function to calculate the midpoint of the interval
	Sets the endpoint to start + 1 to conformt to the bed format standard.
	'''
	

	#print "before midpoint: " + str(interval)
	i = pb_midpoint(interval)
	#print "after  midpoint: " + str(i)
	i.end = i.start + 1
	#print "after endpoint +1" + str(i)
	return i

	

def generate_background(foipath,gfpath,background):
	"""accepts a background filepath
	generate a background and returns as a pybedtool.
	Replaces the chrom fields of the foi and the gf with the interval
	id from the background.
	"""
	bckg = BedTool(str(background))
	bckgnamed = "" 
	interval = 0 

	#inserts a unique interval id into the backgrounds name field
	for b in bckg:
		bckgnamed +=  "\t".join(b[:3])+'\t{}\t'.format(interval) + "\t".join(b[4:]) + "\n"
		interval += 1
	bckg = BedTool(bckgnamed,from_string=True)
	foi = BedTool(str(foipath))
	gf = BedTool(str(gfpath))
	# get the interval names from the background that the gf intersects with
	gf = bckg.intersect(gf)
	gfnamed = ""

	# insert the interval id into the chrom field of the gf and creates a new bedtool
	for g in gf:
		gfnamed += '{}\t'.format(g.name) + "\t".join(g[1:]) + "\n"
		#print "GFNAMED: " + str(g)
	gf = BedTool(gfnamed,from_string=True)
	#print "GFBEDTOOL: " + str(g)

	# inserts the interval id into the chrom column of the foi and creates a new bedtool
	foi = bckg.intersect(foi)
	foinamed = ""
	for f in foi:
		foinamed += '{}\t'.format(f.name) + "\t".join(f[1:])+"\n" 
		#print "FOINAMED: " + str(f)
	foi = BedTool(foinamed,from_string=True)

	#print "FOIBEDTOOL: " + str(f)
	bckgnamed = ""
	for b in bckg:
		bckgnamed += '{}\t'.format(b.name) + "\t".join(b[1:])+"\n"
	bckg = BedTool(bckgnamed,from_string=True)
	# converts the background to a genome dictionary
	chrstartend = [(g.start,g.end) for g in bckg]
	background = dict(zip([g.chrom for g in bckg],chrstartend))
	return {"foi": foi,"gf":gf,"background":background}


	

def run_enrichments(id, f, gfeatures,background, niter, name, score, strand,organism):
	"""
	Run one FOI file (f) against multiple GFs, then 
	save the result to the "results" directory.
	"""
	# sets up logging for the run
	hdlr_id_file = logging.FileHandler(os.path.join("results",str(id)+".log"))
	logger.addHandler(hdlr_id_file)

	try:
		enrichments = []
		# these are progress values that are written to the progress file
		global curprog 
		curprog = 0
		global progmax
		progmax =len(gfeatures)
		for gf in gfeatures:
			write_progress(id, "RUNNING ENRICHMENT ANALYSIS FOR: {}".format(gf))
			e = enrichment(id,f,gf,background,organism,name,score,strand,niter)
			enrichments.append(e)
			path = os.path.join("results", str(id))
			print "writing output"
			with open(path, "wb") as strm:
				cPickle.dump(enrichments, strm)
			curprog += 1
		write_progress(id, "FINISHED")
	except Exception, e:
		logger.error(e)
		logger.error(trace.format_exc())
		write_progress(id,"ERROR: The run crashed: {}".format(e))


def write_progress(id,line):
	"""Saves the current progress to the progress file
	"""

	path = os.path.join("results",str(id)+".prog")
	progress = {"status": line, "curprog": curprog,"progmax": progmax}
	with open(path,"wb") as progfile:
		progfile.write(json.dumps(progress))

		
def get_progress(id):
	"""returns the progress from the progress file
	"""

	path = os.path.join("results",str(id) + ".prog")
	if os.path.exists(path):
		return open(path).read()
	else:
		return ""

