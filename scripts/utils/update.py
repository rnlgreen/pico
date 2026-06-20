""" Functions to update the code on the device from an FTP server """
import secrets
import uos # type: ignore # pylint: disable=import-error

#Import my supporting code
from utils import ftp
from utils import log

# Critical files that should be backed up before updating
CRITICAL_FILES = ['main.py']  # Add pico-specific files if needed (e.g., 'pico0.py', 'pico1.py')

#Check if a local folder exists
def dir_exists(foldername):
    """Function to test if a file exists"""
    try:
        return (uos.stat(foldername)[0] & 0x8000) == 0
    except OSError:
        return False

def file_exists(filename):
    """Check if a file exists"""
    try:
        uos.stat(filename)
        return True
    except OSError:
        return False

def syntax_check(filepath):
    """
    Check if a Python file has valid syntax
    Returns: (success, error_message)
    """
    try:
        with open(filepath, "r") as f: # pylint: disable=unspecified-encoding
            code = f.read()
        compile(code, filepath, "exec")
        return True, None
    except Exception as e: # pylint: disable=broad-except
        import io  # pylint: disable=import-outside-toplevel
        import sys # pylint: disable=import-outside-toplevel
        output = io.StringIO()
        sys.print_exception(e, output) # pylint: disable=maybe-no-member
        e_str = output.getvalue()
        output.close()
        return False, e_str

def backup_file(filepath):
    """
    Create a backup of a file by copying it to filepath.backup
    Returns: True if successful, False otherwise
    """
    backup_path = f"{filepath}.backup"
    try:
        if file_exists(filepath):
            # Read original file
            with open(filepath, "rb") as f:
                content = f.read()
            # Write backup
            with open(backup_path, "wb") as f:
                f.write(content)
            log.status(f"Backed up {filepath}")
            return True
        return False
    except Exception as e: # pylint: disable=broad-except
        log.status(f"Failed to backup {filepath}: {e}", logit=True)
        return False

def restore_backup(filepath):
    """
    Restore a file from its backup
    Returns: True if successful, False otherwise
    """
    backup_path = f"{filepath}.backup"
    try:
        if file_exists(backup_path):
            # Read backup file
            with open(backup_path, "rb") as f:
                content = f.read()
            # Write to original location
            with open(filepath, "wb") as f:
                f.write(content)
            log.status(f"Restored {filepath} from backup", logit=True)
            return True
        else:
            log.status(f"No backup found for {filepath}", logit=True)
            return False
    except Exception as e: # pylint: disable=broad-except
        log.status(f"Failed to restore {filepath}: {e}", logit=True)
        return False

def verify_and_rollback_if_needed(filepath):
    """
    Check syntax of a file and rollback to backup if it fails
    Returns: (is_valid, error_message)
    """
    is_valid, error_msg = syntax_check(filepath)

    if not is_valid:
        log.status(f"SYNTAX ERROR in {filepath}!", logit=True)
        log.status(f"Error: {error_msg}", logit=True)
        #Send alert to Slack that a rollback is happening
        from utils import slack  # pylint: disable=import-outside-toplevel
        slack.send_msg("pico", f":warning: Syntax error detected in {filepath}. Rolling back to previous version.")

        # Attempt to restore from backup
        if restore_backup(filepath):
            log.status(f"Successfully rolled back {filepath} to previous version", logit=True)
            return False, f"Syntax error detected and rolled back: {error_msg}"
        else:
            log.status(f"CRITICAL: Could not restore {filepath} from backup!", logit=True)
            return False, f"Syntax error AND rollback failed: {error_msg}"

    return True, None

#Function to check for new code and download it from FTP site
def update(cleanup=False, skip_syntax_check=False):
    """
    Function to update new code if there is any
    
    Args:
        cleanup: If True, remove local files not present on server
        skip_syntax_check: If True, skip syntax checking (not recommended)
    
    Returns:
        totalfiles: Number of files updated (negative if syntax errors occurred)
    """
    log.status("Checking for new code")
    totalfiles = 0
    critical_files_updated = []
    syntax_errors = []

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

            # Before updating, backup critical files
            for critical_file in CRITICAL_FILES:
                if file_exists(critical_file):
                    backup_file(critical_file)

            #log.status(f"Checking folders: {folders}",logit=True)
            for source in (folders):
                ftp.cwd(session,'/pico/scripts')
                if not dir_exists(source):
                    log.status(f"Creating new folder {source}", logit=True)
                    uos.mkdir(source)

                numfiles = ftp.get_changedfiles(session,source,cleanup)
                totalfiles += numfiles

                # Check which files were actually updated
                if numfiles > 0:
                    files_after = set(uos.listdir(source)) if dir_exists(source) else set()

                    # Identify newly updated files
                    for critical_file in CRITICAL_FILES:
                        file_in_folder = critical_file if source == "." else None
                        if file_in_folder and file_in_folder in files_after:
                            full_path = critical_file if source == "." else f"{source}/{critical_file}"
                            if file_exists(full_path):
                                critical_files_updated.append(full_path)

            ftp.ftpquit(session)

            # Now verify all critical files that were updated
            if not skip_syntax_check and critical_files_updated:
                log.status(f"Checking syntax of {len(critical_files_updated)} critical file(s)...")
                for filepath in critical_files_updated:
                    is_valid, error_msg = verify_and_rollback_if_needed(filepath)
                    if not is_valid:
                        syntax_errors.append((filepath, error_msg))

            # Report results
            if syntax_errors:
                log.status(f"WARNING: {len(syntax_errors)} file(s) had syntax errors and were rolled back", logit=True)
                for filepath, error_msg in syntax_errors:
                    log.status(f"  - {filepath}: {error_msg[:100]}...", logit=True)
                return -len(syntax_errors)  # Return negative number to indicate errors
            elif totalfiles > 0:
                log.status(f"Updated {totalfiles} files successfully", logit=True)
            else:
                #pass
                log.status("No new files found")
        else:
            log.status("FTP error occurred", logit=True)
    except Exception as e: # pylint: disable=broad-except
        log.status("Failed during reload", logit=True, handling_exception=True)
        log.log_exception(e)

    return totalfiles

def manual_backup(filepath):
    """
    Manually create a backup of a file
    Useful for creating initial backups of critical files
    """
    return backup_file(filepath)

def manual_restore(filepath):
    """
    Manually restore a file from backup
    Useful for emergency recovery
    """
    return restore_backup(filepath)

def check_file_syntax(filepath):
    """
    Manually check syntax of a file without rollback
    Returns: (is_valid, error_message)
    """
    return syntax_check(filepath)
