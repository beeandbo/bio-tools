#!/usr/bin/python

from ftplib import FTP
import sys
import re
import os
import subprocess

FTP_SERVER = 'ftp-trace.ncbi.nih.gov'
FTP_BASE_DIR = '/sra/sra-instant/reads/ByExp/sra'

DOWNLOAD_DIR = 'downloads'
FASTQ_DIR = 'fastq'
FASTA_DIR = 'fasta'

# Recursively descend into ftp directories to find experiment
def find_experiment(ftp, accession):
    
    accession = accession.upper()        
    exact = None
    while not exact:

        files = ftp.nlst()
        matches = [f for f in files if accession.startswith(f.upper())]
        if len(matches) == 0:
            current = ftp.pwd().split('/')[-1]
            print "Unable to find accession %s.  Stopped search at directory %s" % (accession, current)
            sys.exit(-1)
    
        for f in matches:
            if f == accession:
                exact = f
                break
        
        if not exact:
            ftp.cwd(matches[0])
        
    path = ftp.pwd() + '/' + exact
    print "Found expirement at %s" % (path,)

    ftp.cwd(exact)
    return path

# Recursively scans experiment directory for all downloadable files
# Recursively downloads all directories with .sra from current working directory
def find_reads(ftp, path = '.'):
    current_dir = ftp.pwd()
    ftp.cwd(path)
    files = ftp.nlst()

    to_download = [f for f in files if re.match(r'.*\.sra', f, re.I)]
    to_recurse = set(files) - set(to_download)           

    results = ['ftp://' + FTP_SERVER + os.path.join(current_dir, path, f) for f in to_download] + sum([find_reads(ftp, directory) for directory in to_recurse], [])

    ftp.cwd(current_dir) # restore directory
    return results

# MAIN
# ----


if(len(sys.argv) <= 1):
    print "Please provide an accession number for download"
    sys.exit(-1)

accession = sys.argv[1]
ftp = FTP(FTP_SERVER, 'anonymous', '')

# Find experiment directory
ftp.cwd(FTP_BASE_DIR)
path = find_experiment(ftp, accession)

# Make download directory
download_dir = os.path.join(DOWNLOAD_DIR, accession)
try:
    os.makedirs(download_dir)
except:
    pass

# Download
to_download = find_reads(ftp)
for f in to_download:
    to_path = os.path.join(download_dir, f.split('/')[-1])
    print "Downloading %s -> %s" % (f, to_path)
    subprocess.call(['wget', '-c', '-O', to_path, f], stdout = sys.stdout, stderr = sys.stderr)

# convert to fastq
fastq_dir = os.path.join(FASTQ_DIR, accession)
try:
    os.makedirs(fastq_dir)
except:
    pass

to_convert = [os.path.join(download_dir, f.split('/')[-1]) for f in to_download]
for f in to_convert:
    to_file = os.path.join(fastq_dir, f.split('/')[-1].replace('.sra', '.fasta'))
    print "Converting %s to %s using fastq-dump (fastq) piped to pearl (fasta)" % (f, to_file)
    subprocess.call(['fastq-dump', '-O', fastq_dir, f], stdout = sys.stdout, stderr = sys.stderr)
    
# # convert to fasta
fasta_dir = os.path.join(FASTA_DIR, accession)
try:
    os.makedirs(fasta_dir)
except:
    pass
for root, dirs, files in os.walk(fastq_dir):
    for f in files:
        from_path = os.path.join(root, f)
        to_path = os.path.normpath(os.path.join(fasta_dir, os.path.relpath(root, fastq_dir), f.replace('.fastq', '.fasta')))        
        print "Converting %s to %s using pearl" % (from_path, to_path)
        
        # See http://edwards.sdsu.edu/labsite/index.php/robert/289-how-to-convert-fastq-to-fasta
        subprocess.call(['perl', '-e', "$i=0;while(<>){if(/^\@/&&$i==0){s/^\@/\>/;print;}elsif($i==1){print;$i=-3}$i++;}"], stdin = open(from_path, 'r'), stdout = open(to_path, 'wb'), stderr = sys.stderr)
    
