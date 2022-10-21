#FTP Utils
import utils.wifi as wifi
from utils.ftplib import FTP

def login(ftphost,ftpuser,ftppw):
    print("Opening FTP connection...")
    try:
        ftp = FTP(ftphost)
        ftp.login(ftpuser,ftppw)
        return ftp
    except Exception as e:
        print("Failed to connect to FTP server: {}".format(e))
        return False

def get_textfile(ftp,folder,filename):
    fp = open(folder+"/"+filename, 'w')
    ftp.retrlines('RETR ' + filename, lambda s, w = fp.write: w(s + '\n'))
    fp.close()

def get_allfiles(ftp,folder):
    ftp.cwd(folder)
    #ftp.retrlines('LIST')
    filenames = ftp.nlst()
    numfiles = 0
    for filename in filenames:
        #Try getting file size to see if it is a directory
        try:
            ftp.size(filename)
            print("Getting file {}".format(filename))
            get_textfile(ftp,folder,filename)
            numfiles+=1
        except:
            print("Skipping '{}'".format(filename))
    return numfiles

def cwd(ftp,folder):
    ftp.cwd(folder)

def quit(ftp):
    ftp.quit()

