""" Functions to update the code on the device from an FTP server """
import secrets
import uos # type: ignore # pylint: disable=import-error

#Import my supporting code
from utils import ftp
from utils import log

#Check if a local folder exists
def dir_exists(foldername):
    """Function to test if a file exists"""
    try:
        return (uos.stat(foldername)[0] & 0x8000) == 0
    except OSError:
        return False

#Function to check for new code and download it from FTP site
def update(cleanup=False):
    """Function to update new code if there is any"""
    log.status("Checking for new code")
    totalfiles = 0
    try:
        session = ftp.login(secrets.ftphost,secrets.ftpuser,secrets.ftppw)
        if session:
            #Check all the folders for new files
            folders = ["."]
            # Get parent folders
            ftp.cwd(session,'/pico/scripts')
            folders += ftp.list_folders(session)
            # Get sub folders
            subfolders = []
            for source in (folders):
                if source != '.':
                    ftp.cwd(session,f'/pico/scripts/{source}')
                    subfolderlist = []
                    subfolderlist += ftp.list_folders(session)
                    for f in subfolderlist:
                        subfolders.append(f"{source}/{f}")
            folders += subfolders
            #log.status(f"Checking folders: {folders}",logit=True)
            for source in (folders):
                ftp.cwd(session,'/pico/scripts')
                if not dir_exists(source):
                    log.status(f"Creating new folder {source}", logit=True)
                    uos.mkdir(source)
                numfiles = ftp.get_changedfiles(session,source,cleanup)
                totalfiles += numfiles
            ftp.ftpquit(session)
            if totalfiles > 0:
                log.status(f"Updated {totalfiles} files", logit=True)
            else:
                #pass
                log.status("No new files found")
        else:
            log.status("FTP error occurred", logit=True)
    except Exception as e: # pylint: disable=broad-except
        log.status("Failed during reload", logit=True, handling_exception=True)
        log.log_exception(e)
    return totalfiles
