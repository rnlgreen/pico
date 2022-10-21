#Test FTP script
import utils.wifi as wifi
from utils.ftplib import FTP
import secrets

def get_textfile(folder,filename):
    fp = open(folder+"/"+filename, 'w')
    ftp.retrlines('RETR ' + filename, lambda s, w = fp.write: w(s + '\n'))
    fp.close()

def get_allfiles(folder):
    ftp.cwd(folder)
    #ftp.retrlines('LIST')
    filenames = ftp.nlst()
    numfiles = 0
    for filename in filenames:
        #Try getting file size to see if it is a directory
        try:
            ftp.size(filename)
            print("Getting file {}".format(filename))
            get_textfile(folder,filename)
            numfiles+=1
        except:
            print("Skipping '{}'".format(filename))
    return numfiles

def cwd(folder):
    ftp.cwd(folder)

def quit():
    ftp.quit()

print("Opening FTP connection...")
ftp = FTP(secrets.ftphost)
ftp.login(secrets.ftpuser,secrets.ftppw)

