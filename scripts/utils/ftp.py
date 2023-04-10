#FTP Utils
from ftplib import FTP
from utils.sha256 import check_sha256
import utils.myid as myid
import utils.mqtt as mqtt
import os

cleanup = False

def login(ftphost,ftpuser,ftppw):
    #status("Opening FTP connection")
    try:
        ftp = FTP(ftphost)
        ftp.login(ftpuser,ftppw)
        return ftp
    except Exception as e:
        status("Failed to connect to FTP server: {}".format(e))
        return False

#status and send status messages
def status(message):
    print(message)
    message = myid.pico + ": " + message
    topic = 'pico/'+myid.pico+'/status'
    if mqtt.client != False:
        mqtt.send_mqtt(topic,message)

def get_textfile(ftp,folder,filename):
    fp = open(folder+"/"+filename, 'w')
    ftp.retrlines('RETR ' + filename, lambda s, w = fp.write: w(s + '\n'))
    fp.close()

def get_binaryfile(ftp,folder,filename):
    with open(folder+"/"+filename, 'wb') as fp:
        ftp.retrbinary('RETR ' + filename, fp.write)

def get_sha256_list(ftp):
    lines = []
    ftp.retrlines('RETR sha256.txt', lines.append)
    sha256_values = {}
    for line in lines:
        sha256value,filename = line.strip().split('  ')
        sha256_values[filename] = sha256value
    return sha256_values

def get_allfiles(ftp,folder):
    ftp.cwd(folder)
    #ftp.retrlines('LIST')
    filenames = ftp.nlst()
    numfiles = 0
    for filename in filenames:
        #Try getting file size to see if it is a directory
        try:
            ftp.size(filename)
            status("Getting {}".format(filename))
            #get_textfile(ftp,folder,filename)
            get_binaryfile(ftp,folder,filename)
            numfiles+=1
        except:
            status("Failed '{}'".format(filename))
    return numfiles

def get_changedfiles(ftp,folder):
    ftp.cwd(folder)
    numfiles = 0
    sha256_values = get_sha256_list(ftp)
    for filename in sha256_values:
        #Get compare sha256 values
        if not check_sha256(folder+"/"+filename, sha256_values[filename]):
            #Try getting file size to see if it is a directory
            try:
                ftp.size(filename)
                status("Getting {}".format(folder+"/"+filename))
                get_binaryfile(ftp,folder,filename)
                numfiles+=1
            except:
                status("File not found: '{}'".format(folder+"/"+filename))
    if cleanup:
        localfiles = os.listdir(folder)
        for filename in localfiles:
            if filename.endswith(".py") and not filename in sha256_values.keys():
                status("Removing file {}".format(filename))
                os.remove(folder+"/"+filename)
    return numfiles

def cwd(ftp,folder):
    ftp.cwd(folder)

def quit(ftp):
    ftp.quit()
