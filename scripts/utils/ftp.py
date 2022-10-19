#Test FTP script
import utils.wifi as wifi
from utils.ftplib import FTP

wifi.wlan_connect('pico1')

def get_textfile(folder,filename):
    fp = open(folder+"/"+filename, 'w')
    ftp.retrlines('RETR ' + filename, lambda s, w = fp.write: w(s + '\n'))
    fp.close()

def get_allfiles(folder):
    ftp.cwd(folder)
    ftp.retrlines('LIST')
    filenames = ftp.nlst()
    for filename in filenames:
        #Try getting file size to see if it is a directory
        try:
            ftp.size(filename)
            print("Getting file {}".format(filename))
            get_textfile(folder,filename)
        except:
            print("Skipping '{}'".format(filename))

ftp = FTP('192.168.1.113')
ftp.login("pi","Pepperm1nt")
ftp.cwd('files')
get_allfiles(".")
get_allfiles("utils")
ftp.quit()
