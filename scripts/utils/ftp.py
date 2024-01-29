#FTP Utils
import os
from ftplib import FTP
from utils.sha256 import check_sha256
from utils import myid
from utils import mqtt

cleanup = False

def login(ftphost,ftpuser,ftppw):
    #status("Opening FTP connection")
    try:
        ftp = FTP(ftphost)
        ftp.login(ftpuser,ftppw)
        return ftp
    except Exception as e: # pylint: disable=broad-exception-caught
        status(f"Failed to connect to FTP server: {e}")
        return False

#status and send status messages
def status(message):
    print(message)
    message = myid.pico + ": " + message
    topic = 'pico/'+myid.pico+'/status'
    if mqtt.client is not False:
        mqtt.send_mqtt(topic,message)

#Fetch text files (ascii crlf conversion) (not actually used by anything at the moment)
def get_textfile(ftp,folder,filename):
    fp = open(folder+"/"+filename, 'w', encoding='utf-8')
    ftp.retrlines('RETR ' + filename, lambda s, w = fp.write: w(s + '\n'))
    fp.close()

#Fetch binary files
def get_binaryfile(ftp,folder,filename):
    with open(folder+"/"+filename, 'wb') as fp:
        ftp.retrbinary('RETR ' + filename, fp.write)

#Send binary files
def put_binaryfile(ftp,folder,filename):
    with open(folder+"/"+filename, 'rb') as fp:
        target_file = filename + "_" + myid.pico
        ftp.storbinary('STOR ' + target_file, fp)

#Get the server side list of sha256 values for available code
def get_sha256_list(ftp):
    lines = []
    ftp.retrlines('RETR sha256.txt', lines.append)
    sha256_values = {}
    for line in lines:
        sha256value,filename = line.strip().split('  ')
        sha256_values[filename] = sha256value
    return sha256_values

#Get all the files on a folder (not actually used by anything at the moment)
def get_allfiles(ftp,folder):
    ftp.cwd(folder)
    #ftp.retrlines('LIST')
    filenames = ftp.nlst()
    numfiles = 0
    for filename in filenames:
        #Try getting file size to see if it is a directory
        try:
            ftp.size(filename)
            status(f"Getting {filename}")
            #get_textfile(ftp,folder,filename)
            get_binaryfile(ftp,folder,filename)
            numfiles+=1
        except: # pylint: disable=bare-except
            status(f"Failed '{filename}'")
    return numfiles

#Get any missing or changed files
def get_changedfiles(ftp,folder):
    ftp.cwd(folder)
    numfiles = 0
    sha256_values = get_sha256_list(ftp)
    for filename in sha256_values: # pylint: disable=consider-using-dict-items
        #Get compare sha256 values
        if not check_sha256(folder+"/"+filename, sha256_values[filename]):
            #Try getting file size to see if it is a directory
            try:
                ftp.size(filename)
                status(f"Getting {folder + '/' + filename}")
                get_binaryfile(ftp,folder,filename)
                numfiles+=1
            except: # pylint: disable=bare-except
                status(f"File not found: '{folder + '/' + filename}'")
    if cleanup:
        localfiles = os.listdir(folder)
        for filename in localfiles:
            if filename.endswith(".py") and not filename in sha256_values.keys():  # pylint: disable=consider-iterating-dictionary
                status(f"Removing file {filename}")
                os.remove(folder+"/"+filename)
    return numfiles

def cwd(ftp,folder):
    ftp.cwd(folder)

#Returns something like this:
#-rwxrwxrwx   1 1000     1000              746 Jan 28 11:28 generate_sha256.sh
#drwxrwxrwx   1 1000     1000               70 Mar 26  2023 lib
#-rwxrwxrwx   1 1000     1000             7483 Jan 28 11:30 main.py
#-rwxrwxrwx   1 richard  users            3833 Dec 04  2023 pico0.py
def list_folders(ftp):
    listing = []
    folders = []
    ftp.retrlines('list', listing.append)
    for line in listing:
        if line.startswith("d"):
            folder = line.split()[8]
            folders.append(folder)
    return folders

def ftpquit(ftp):
    ftp.quit()
