#ftp test
import secrets

def reload():
    import utils.ftp as ftp
    session = ftp.login(secrets.ftphost,secrets.ftpuser,secrets.ftppw)
    if session:
        #Move to the root FTP folder
        ftp.cwd(session,'/pico/scripts')
        #Get all files for the root
        numfiles = ftp.get_allfiles(session,".")
        #Get all files for utils (get_allfiles will deal with changing directory)
        numfiles = ftp.get_allfiles(session,"utils")
        ftp.quit(session)
    else:
        print("FTP error occurred.")

if __name__ == "__main__":
    reload()
